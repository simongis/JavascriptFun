from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
from arcgis.geocoding import geocode

# Globals
headers = ({'User-Agent':
        'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'})
url = 'https://www.realestate.com.au/sold/property-house-between-600000-800000-in-seddon,+vic+3011%3b+ascot+vale,+vic+3032%3b+brunswick+west,+vic+3055%3b+coburg,+vic+3058%3b+footscray,+vic+3011%3b+moonee+ponds,+vic+3039%3b+travancore,+vic+3032%3b+maidstone,+vic+3012/list-1?numBaths=1&includeSurrounding=false&activeSort=solddate'

def main():
    # Go fetch latest sold results with a hard baked query URL parameter to RealEstate.com.au
    scrape_result = scrape() # returns a dataframe
    print("Finished Scraping and putting into a Pandas DF")
    # ToDo loop through each listing to get Image URL
    # Geocode DF
    print('Geocoding...')
    geocoded = get_address(scrape_result) # returns a dataframe
    print('Finished Geocoding')
    # ToDo Tidy up Date Field
    # ToDo COmpare with results on ArcGIS Online, and append?
    

def get_address(df):         
     # Add X, Y Columns to DF
     df['X'] = ""
     df['Y'] = ""
          
     for index, row in df.iterrows():
         input_address = (row['Address'] + ", " + row['Suburb'] + ", " + "Victoria, Australia")     
         geocode_result = geocode(input_address)
         if geocode_result is None:
             continue
         else:
             df.loc[index, 'X'] = geocode_result[0]['location']['x']
             df.loc[index, 'Y'] = geocode_result[0]['location']['y']
     df.to_csv("Output.csv")
     return df
    
                      
    
    
def scrape():
    r=requests.get(url,headers=headers)
    c=r.content
    soup=BeautifulSoup(c,"html.parser")
    
    raw_num_results = soup.findAll("div",{"class":"results-set-header__results"})[0].text
    num_results = re.search('of (.+?) results', raw_num_results).group(1)
    page_nr = -(-int(num_results)//25) #use negatives and floor division to round up (without having to import math functions)
    print("Total pages: " + str(page_nr))
    l=[]
    # for page in range(1,page_nr+1):  # Dont need to loop through every page for this scrape
    for page in range(0,2):
        
        base_url='https://www.realestate.com.au/sold/property-house-between-600000-800000-in-seddon,+vic+3011%3b+ascot+vale,+vic+3032%3b+brunswick+west,+vic+3055%3b+coburg,+vic+3058%3b+footscray,+vic+3011%3b+moonee+ponds,+vic+3039%3b+travancore,+vic+3032%3b+maidstone,+vic+3012/list-' + str(page) +'??numBaths=1&includeSurrounding=false&activeSort=solddate'
        r=requests.get(base_url,headers=headers)
        c=r.content
        soup=BeautifulSoup(c,"html.parser")
        #all=soup.find_all("div",{"class":"residential-card__content"})
        all=soup.select('.results-card') # Pluck out the listings
        
    
        for item in all:
            d={}
            #address = str.split(item.find("h2",{"class":"residential-card__address-heading"}).text,", ")
            address = item.find(class_='residential-card__info-text')
            if address is None:
                address = ''
                continue
            else:
                address = address.text
                address = str.split(str(address), ", ")
                d["Address"] = address[0]
                d["Suburb"] = address[1]
            
            price = item.find("span",{"class":"property-price"}).text
            
            if price is None:
                price = 0
                continue # skip this listing, only care if there is a price
            else:
                price = price[1:] # Remove dollar
                price = price.replace(',', '') # Remove comma
            d["Price"] = price
            
            sold_date = item.find(class_='residential-card__secondary-text rui-truncate')
            # sold_date = item.find(class_='residential-card__with-comma')  # This changed
            if sold_date is None:
                sold_date = ''
            else:
                sold_date = (sold_date.get_text()[-11:])
            d["SoldDate"] = sold_date
       
            attributes=("beds","baths","cars")
            for attribute in attributes:
                try:
                    d[attribute]=item.find("span",{"class":"general-features__icon general-features__"+attribute}).text                                    
                except:
                    d[attribute]="None"
                        
            prop_url = item.find(class_='details-link')
            if prop_url is None:
                prop_url = ''
            else:
                prop_url = 'https://www.realestate.com.au' + prop_url['href']
            d["URL"] =  prop_url
            
            l.append(d)
        
    df=pd.DataFrame(l)
    # df.to_csv("Output.csv")
    return df

# entry point
if __name__ == "__main__":
    main()
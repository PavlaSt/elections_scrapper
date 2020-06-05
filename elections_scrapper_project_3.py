
from bs4 import BeautifulSoup as BS
import requests
import csv
import time

#===================================================================
def has_headers_but_no_class(tag):
    return tag.has_attr('headers') and not tag.has_attr('class')

def soup_maker(url):
	done=False
	while done==False:
		try:
			print('<-', end='', flush=True)
			r = requests.get(url)
			print('->', end='', flush=True)
		except Exception as e:
			print('\n!!! Attention !!! Exception !!!\n', flush=True)
			print(e, flush=True)	
			time.sleep(30)
			print('\n... Continuing...\n ', flush=True)
		else:
			html=r.text
			soup=BS(r.text, "html.parser")
			done=True
	return soup

def keys_values_extractor(soup, d):
	#Extracting count of registred voters, data cleaning, inserting into a dictionary
	voters=soup.find(headers="sa2")
	voters2=voters.string
	d['Voliči v seznamu']=voters2.replace(u'\xa0', u'')

	#Extracting count of distributed envelops, data cleaning, inserting into a dictionary
	envelope=soup.find(headers="sa3")
	envelope2=envelope.string
	d['Vydané obálky']=envelope2.replace(u'\xa0', u'')		
			
	##Extracting sum of valid votes, data cleaning, inserting into a dictionary
	valid_votes=soup.find(headers="sa6")
	valid_votes2=valid_votes.string
	d['Platné hlasy']=valid_votes2.replace(u'\xa0', u'')
	
	#Extracting count of votes, data cleaning
	votes=[]
	votes2=[]
	clean_votes=[]
	votes+=soup.find_all(headers="t1sa2 t1sb3")
	votes+=soup.find_all(headers="t2sa2 t2sb3")
	for vote in votes:
		votes2+=(vote.contents)
	for vote in votes2:
		clean_votes.append(vote.replace(u'\xa0', u''))

	#Extracting namest of parties
	parties=soup.find_all(has_headers_but_no_class)
	parties2=[]
	for party in parties:
		parties2+=(party.contents)
	
	#Updating dictionary with party:votes pairs
	for j in range(len(parties2)):
		d[parties2[j]]=clean_votes[j]
	return(d)	

def dict_csv_writer(header, lst_d):
	with open('volby.csv','a+',newline='') as file:
		writer = csv.DictWriter(file,header)
		writer.writerows(lst_d)
		file.flush()
	return print('\nData saved.')

#===================================================================
def main():
	start_time = time.time()
	print()

	#Making of CSV header
	header=['Kód','Obec','Voliči v seznamu', 'Vydané obálky', 'Platné hlasy']
	with open('volby.csv','a+',newline='') as file:

		#Extracting names of parties from summary result web page
		soup=soup_maker(url='https://volby.cz/pls/ps2017nss/ps2?xjazyk=CZ')
		parties=soup.find_all(has_headers_but_no_class)
		parties2=[]
		for party in parties:
			parties2+=(party.contents)
		header+=parties2
		writer = csv.DictWriter(file, header)
		writer.writeheader()
		file.flush()
	print('Header finished.', flush=True)

	#Extracting links from given page into a list
	soup=soup_maker(url='https://volby.cz/pls/ps2017nss/ps3?xjazyk=CZ')
	adresses=[]
	a=soup.find_all('a')
	for item in a:
		#Links of interest have 'ps32' in them
		if 'ps32' in str(item):
			adresses.append('https://volby.cz/pls/ps2017nss/'+item['href'])
		#Abroad votes - links of interest have 'ps361' in them
		if 'ps361' in str(item):
			d={}
			soup=soup_maker(url='https://volby.cz/pls/ps2017nss/'+item['href'])
			#Getting keys and values, inserting updated dictionary into a list
			d['Kód']='999999'
			print('\nZAHRANIČÍ', flush=True)
			d['Obec']='Zahraničí'
			updated_d=keys_values_extractor(soup, d)
			lst_d=[]
			lst_d.append(updated_d)
			#Writing list of dictionaries into CSV
			dict_csv_writer(header, lst_d)
			
	#Going trough extracted links
	print('Starting going trough the adresses: ', flush=True)
	for k,item in enumerate(adresses):
		print('\n|',k,'|', flush=True)
		lst_d=[]
		
		#Extracting links from subpages into a list
		adresses2=[]
		soup=soup_maker(url=item)
		
		a=soup.find_all('a')
		for item in a:
			#Links of interest have 'ps311' in them
			if 'ps311' in str(item) and 'https://volby.cz/pls/ps2017nss/'+item['href'] not in adresses2:
				adresses2.append('https://volby.cz/pls/ps2017nss/'+item['href'])
		

		#Going through list of extracted links		
		for i,item in enumerate(adresses2):
			d={}
			soup=soup_maker(url=item)
			
			#Extracting code of municipality, inserting into a dictionary
			ord=item.find('obec=')
			num=item[ord+5:ord+11]
			d={'Kód':num}
			print(num,' ', end='', flush=True)

			#Extracting name of municipality, inserting into a dictionary
			lst=soup.find_all('h3')
			h3_str=lst[-1].string
			obec=h3_str.strip("'\n")
			obec1=obec[6:]
			d['Obec']=obec1

			#Extracting keys and values, inserting updated dictionary into a list
			updated_d=keys_values_extractor(soup, d)
			lst_d.append(updated_d)

		#Writing list of dictionaries into CSV
		dict_csv_writer(header, lst_d)
		
	print()
	elapsed_time = int(time.time() - start_time)
	print(f'The end.\nIt took {elapsed_time//60} min and {elapsed_time%60} sec.')		

#==============================================================================

if __name__ == "__main__":
    main()
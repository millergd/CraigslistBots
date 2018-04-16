import requests
import datetime
from bs4 import BeautifulSoup

import boto3
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource('dynamodb')

class CraigslistItem(object):

	def __init__(self, href, tablename):
		self.info = {
			"link": href,
			"postid": None,
			"currentPrice": None,
			"title": None,
			"activeSince": None,
			"description": None,
			"priceHistory": list(),
		}

		self.tablename = tablename

		self.GetNewData()
		self.UpdateLocalData()
		self.StoreData()
		#self.ExportData()


	def GetNewData(self):

		r  = requests.get(self.info["link"])

		data = r.text

		soup = BeautifulSoup(data)

		try:
			for child in soup.find('div', {"class": "postinginfos"}):
				if "post id" in child.string:
					postid = (child.string).split(" ")[-1]
					print postid
					break
		except:
			postid = "No postid"

		try:
			price = soup.find('span', {"class": "price"}).text
		except:
			price = "No price"

		try:
			title = soup.find('span', {"id": "titletextonly"}).text
		except:
			title = "No title"

		try:
			activeSince = soup.find('time', {"class":"date timeago"}).get('datetime').split("T")[0].replace("-",'')
		except:
			activeSince = "No posting data"

		self._IntegrateNewData(postid, price, title, activeSince)

	def ExportData(self):
		#further develop this
		return self.info

	def UpdateLocalData(self):
		dynamodb = boto3.resource("dynamodb")
		table = dynamodb.Table(self.tablename)

		try:
			result = table.query(KeyConditionExpression=Key('postid').eq(self.info['postid']))
			print "found history!"
			print result
			if result['Items'] and "priceHistory" in result['Items'][0] and result['Items'][0]['priceHistory'] != None:
				self.info['priceHistory'] = result['Items'][0]['priceHistory']
				if self.info['currentPrice'] != str(result['Items'][0]['priceHistory'][-1]):
					print "appending new price"
					self.info['priceHistory'].append(self.info['currentPrice'])

		except:
			print "ERROR"

	def StoreData(self):
		dynamodb = boto3.resource("dynamodb")
		table = dynamodb.Table(self.tablename)

		table.put_item(Item=self.info)


	def _IntegrateNewData(self, postid, price, title, activeSince):
		# further develop this
		self.info["postid"] = postid
		self.info["activeSince"] = activeSince
		self.info["currentPrice"] = price
		self.info["title"] = title
		self.info['priceHistory'] = [self.info['currentPrice']]





class CraigslistBot(object):

	def __init__(self, startpage, tablename):
		self.startPage = startpage
		self.work = []
		self.emailData=''
		self.items = []
		self.tablename = tablename

	def Run(self):
		self.GetWork()
		self.DoWork()
		self.FormatItemsHtml()
		self.SendData()
	
	def GetWork(self):

		r  = requests.get(self.startPage)

		data = r.text

		soup = BeautifulSoup(data)

		for link in soup.find_all('a', {"class": "result-image gallery"}):
			self.work.append(link.get('href'))

	def DoWork(self):
		i = 0
		for link in self.work:
			data = CraigslistItem(link, self.tablename)
			self.items.append(data.ExportData())
			i+=1
			print i

		self.items = sorted(self.items, key=lambda k: k['activeSince']) 

		print self.items

	def FormatItemsString(self):
		for item in self.items:
			self.emailData += ('Post ID: ' + item['postid'] + '\n')
			self.emailData += ('Title: ' + item['title'] + '\n')
			self.emailData += ('Price: ' + item['currentPrice'] + '\n')
			self.emailData += ('Active Since: ' + item['activeSince'][:3] + "-" + item['activeSince'][4:6] + '-' + item['activeSince'][6:] + '\n')
			self.emailData += '\n'
	
	def FormatItemsHtml(self):
		for item in self.items:
			self.emailData += """
				<ul>
					<li>Title: {title}</li>
					<li>PostID: {postid}</li>
					<li>Price: {price}</li>
					<li>History: {history}</li>
					<li>Active Since: {active}</li>
					
				</ul>""".format(postid=item['postid'], title=item['title'], price=item['currentPrice'], history=item['priceHistory'], active=str(item['activeSince']))

	def SendData(self):
		client = boto3.client('ses')

		response = client.send_email(
			Source='gdmill55@gmail.com',
			Destination={
				'ToAddresses': [
					'gdmill55@gmail.com',
				],
			},
			Message={
				'Subject': {
					'Data': 'craigslist',
					'Charset': 'UTF-8'
				},
				'Body': {
					'Text': {
						'Data': self.emailData,
						'Charset': 'UTF-8'
					},
				'Html': {
	                'Data':"""
	                	<html>
						<head></head>
						<body>
						  <h1>Craigslist TVs</h1>
						  <p>{emailData}<p>
						</body>
						</html>
						            """.format(emailData=self.emailData),
	                'Charset': 'UTF-8'
	            	}

				}
			},
		)

		print response

if __name__=="__main__":




	bot = CraigslistBot("https://annarbor.craigslist.org/search/sss?query=tv&sort=rel", "craigslisttv")
	bot.Run()

	with open("lastrun.txt", "w'") as filename:
		filename.write(str(datetime.datetime.now()))

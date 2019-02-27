#!/python27/python
import requests
from datetime import date, timedelta, datetime
from pyquery import PyQuery
import MySQLdb
import os
# import subprocess
import creds
import emails

emailuser = os.environ["GOOGLEADDRESS"]
emailpassword = os.environ["GOOGLEPASSWORD"]
emailname = os.environ["GOOGLENAME"]
emailfrom = emailname + " <" + emailuser + ">"

toaddr = ["mstucka@pbpost.com", "DHofheinz@pbdailynews.com", "JOstrowski@pbpost.com", "eclarke@pbdailynews.com", "adavis@pbdailynews.com", "sdarby@pbdailynews.com", "aclough@pbpost.com"]
# toaddr = ["mstucka@pbpost.com"]   # TESTING


## For multiple values for the same key, requests wants key-value tuples. 

NowDate=date.today()
#OldDate=date.today() - timedelta(1)
OldDate=date.today() - timedelta(15)   # HEY! WAS 15.

FromDate = OldDate.strftime("%m/%d/%Y")
ToDate = NowDate.strftime("%m/%d/%Y")

headers = {'user-agent': 'Palm Beach Post, 561-820-4497'}


payload = [
("search_by", "DocType"),
("search_entry", "D"),
("consideration", "6,000,000"),
("FromDate", FromDate),
("ToDate", ToDate),
("RecSetSize", "2000"),
("PageSize", "2000"),
("ShowProperties", "YES")
]

urlin="http://oris.co.palm-beach.fl.us/or_web1/or_sch_1.asp"
myget = requests.get(urlin, headers=headers)
cookies=myget.cookies

# ## ## create database propertysales character set utf8 collate utf8_general_ci; use propertysales; create table psdarrellmaster (deets varchar(100) PRIMARY KEY, name1 varchar(50), name2 varchar(50), mydate date, doctype varchar(10), book int, page int, cfn varchar(50), legal varchar(50));


# ## Now we know what the site is looking for. Let's respond appropriately.
urlout = "http://oris.co.palm-beach.fl.us/or_web1/new_sch.asp"
myput = requests.post(urlout, data=payload, cookies=cookies, headers=headers)
#print cookies
# #with open('output.csv', 'wb') as handle:
# handle.write(myput.content)
# # print myput.content
pq = PyQuery(myput.content)
### HEY! #pq = PyQuery(filename="full.html")
#print pq
tablecount = len(PyQuery(pq).find('table'))
#print str(tablecount) + " tables found"
cookiejar=requests.utils.dict_from_cookiejar(cookies)
cookiejar.update((k, "") for k,v in cookiejar.iteritems() if v is None)
extras=""
for key in cookiejar:
    extras = extras + "&" + str(key) + "=" + str(cookiejar[key])
#for cookie in cookies:
#print extras   
        


if tablecount == 2:
#if table == None:
    print "No sales found."
else:
    #print table
    table = PyQuery(pq)("table")[5]
    #print PyQuery(table).text()
    dbhost=creds.access['dbhost']
    dbuser=creds.access['dbuser']
    dbpassword=creds.access['dbpassword']
    dbdatabase=creds.access['dbdatabase']
    dbhost=[MySQLdb.connect(host=dbhost, user=dbuser, passwd=dbpassword, db=dbdatabase) for i in range(1)]
    dbconnection=dbhost[0]
    db=dbconnection.cursor()
    # inserterer=dbhost[1]
    # inserter=inserterer.cursor()
    # aaaaaaaaargh=dbhost[2].cursor()
    db.execute("drop table if exists psdarrellstaging")
    db.execute("create table psdarrellstaging like psdarrellmaster")
    for row in PyQuery(table)("tr")[1:]:
        #print row("td")[1].text()
        #row("td")[0].text()
        #print PyQuery(PyQuery(row)("td")[1]).text()
        deets = "".join((PyQuery(PyQuery(row)("td")[0])("a").attr("href")).split())
        name1 = PyQuery(PyQuery(row)("td")[1]).text()
        name2 = PyQuery(PyQuery(row)("td")[2]).text()
        mydate = datetime.strftime(datetime.strptime(PyQuery(PyQuery(row)("td")[3]).text(),"%m/%d/%Y"), "%Y-%m-%d")
        doctype = PyQuery(PyQuery(row)("td")[4]).text()
        book = PyQuery(PyQuery(row)("td")[5]).text()
        page = PyQuery(PyQuery(row)("td")[6]).text()
        cfn = PyQuery(PyQuery(row)("td")[7]).text()
        legal = PyQuery(PyQuery(row)("td")[8]).text()
        id = "|".join([cfn, name1, name2, legal])
        db.execute("insert into psdarrellstaging (deets, name1, name2, mydate, doctype, book, page, cfn, legal, id) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (deets, name1, name2, mydate, doctype, book, page, cfn, legal, id))

    dbconnection.commit()
    # db.execute("delete from psdarrellstaging where deets in (select deets from psdarrellmaster)")
    db.execute("delete from psdarrellstaging where id in (select id from psdarrellmaster)")
    db.execute("""select count(*) from psdarrellstaging""")
    numberofrows=db.fetchone()[0]
    if numberofrows==0:
        print "No new sales found. Let's try again later."
    else: 
        #print(str(len(numberofrows)) + " new rows found. Attempting to insert.")
        print("Attemping to insert some number of rows.")
        db.execute("""insert into psdarrellmaster select * from psdarrellstaging""")
        dbconnection.commit()
        
        outfile = open("c:\git\propertysales\psdarrellreport.html", "w")
        
        outfile.write('<html><body><table width=\"100%\"><tr><td>Sale info</td><td>Party1</td><td>Party2</td><td>Book/Page</td><td>CFN</td><td>Legal description</td></tr>')
        
        db.execute("select * from psdarrellstaging")

        for row in db:
            text='<tr><td><A HREF="http://oris.co.palm-beach.fl.us/or_web1/' + row[0] + extras + '" target="_blank">Details</A></td><td><A HREF="http://oris.co.palm-beach.fl.us/or_web1/new_sch.asp?search_by=Name&search_entry=' + row[1].strip().replace(" ", "+") + '" target="_blank">' + row[1].strip() + '</A></td><td><A HREF="http://oris.co.palm-beach.fl.us/or_web1/new_sch.asp?search_by=Name&search_entry=' + row[2].strip().replace(" ", "+") + '" target="_blank">' + row[2].strip() + '</A></td><td>' + str(row[5]) + "/" + str(row[6]) + '</td><td>' + str(row[7]) + '</td><td>' + row[8] + '</td></tr>'
            outfile.write(text)
        outfile.write('</table></body></html>')
        outfile.close()
        dbconnection.commit()
        print("Attempting to email " + str(len(toaddr)) + " people.")
        subject = "Property sales report"
        html = open("c:\git\propertysales\psdarrellreport.html", "r")
        message = emails.html(html=html,
                  subject=subject,
                  mail_from=emailfrom)
        message.send(to=(toaddr), smtp={"host":"smtp.gmail.com", "port":465, "ssl":True, "user":emailuser, "password":emailpassword} )
        ### Only email if new records are found.

    dbconnection.commit()
    db.close()
    dbconnection.close()


#print cookies

#!/usr/bin/python

import socket
import argparse
import MySQLdb as mysql
import smtplib
import email.utils
from email.mime.text import MIMEText
import sys
import cStringIO
import time



class start():
	
	def __init__(self):
		self.db_host = 'localhost'
		self.db_user = 'bgpmon'
		self.db_pass = 'bgpmon'
		self.db = 'bgpmon'
#		sys.stdout = open('/var/log/bgp-mon.log','a')
		pass

	def sql_conn(self):
		try:
			self.conn = mysql.connect(self.db_host,self.db_user,self.db_pass,self.db)
	
		except mysql.Error, self.e:
	
			print "Error %d:%s" % (self.e.args[0], self.e.args[1])
			sys.exit(1)
	

	def sql_populate(self,b=None):
			
		if b:
			self.table = 'base_line'
			self.cur = self.conn.cursor()
				
			self.cur.execute("select * from %s where network = (select id from watched where network = %%s)" % self.table, (self.info))
			if self.cur.fetchone() == None:

				self.cur.execute("insert into %s (network) values ((select id from watched where network = %%s))" % self.table, (self.info))

				self.cur.execute("update %s set Origin_AS = %%s, IP = %%s, BGP_prefix = %%s, CC = %%s, Registry = %%s, Allocated = %%s, AS_Name = %%s, time_stamp=NOW() where network = (select id from watched where network = %%s)" % self.table, (self.origin_AS,self.IP,self.BGP_prefix,self.CC,self.Registry,self.Allocated,self.AS_name,self.info))

			else:
				self.cur.execute("update %s set Origin_AS = %%s, IP = %%s, BGP_prefix = %%s, CC = %%s, Registry = %%s, Allocated = %%s, AS_Name = %%s, time_stamp=NOW() where network = (select id from watched where network = %%s)" % self.table, (self.origin_AS,self.IP,self.BGP_prefix,self.CC,self.Registry,self.Allocated,self.AS_name,self.info))
			
			self.conn.commit()
		
		else:
			self.table = 'latest_update'
                        self.cur = self.conn.cursor()

			print '[*] Adding Entry to latest_update'
                        self.cur.execute("insert into %s (network,Origin_AS,IP,BGP_prefix,CC,Registry,Allocated,AS_Name) values ((select id from watched where network like %%s),%%s,%%s,%%s,%%s,%%s,%%s,%%s)" % self.table, (self.info,self.origin_AS,self.IP,self.BGP_prefix,self.CC,self.Registry,self.Allocated,self.AS_name))
                
			self.conn.commit()
			
	def myrecv(self,timeout=2):
		# make socket non-blocking i.e. if no data is recieved break connection
		self.connection.setblocking(0)	
		# total data in an array
		self.total_reply=[]
		self.rdata= ''
		#begining time
		self.begin=time.time()
		while True:
			# if we get some data, then break after time out
			if self.total_reply and time.time()-self.begin>timeout:
				break
			# if we didnt get any data break after timeout*2
			elif time.time()-self.begin>timeout*2:
				break
			# recive data
			try:
				self.rdata = self.connection.recv(2048)
				if self.rdata:
					self.total_reply.append(self.rdata)
					#reset the begining time
					self.begin = time.time()
				else:
					# sleep for sometime to indicate gap
					time.sleep(0.1)
			except:
				pass
		#join all parts to make final reply
		return ''.join(self.total_reply)


	def magic(self, b=None):

		self.sql_conn()
		self.cur = self.conn.cursor()
		self.cur.execute('select network from watched')
		self.buffer = 'begin\r\nverbose\r\nend'
		print "[*] Querying Team Cymru Whois Server for Orignating AS"
		for self.query in self.cur:
			self.index = self.buffer.index('end')
			self.buffer = self.buffer[0:self.index] + self.query[0] + ' ' + self.query[0] + '\r\n' + self.buffer[self.index:]
		self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	#	print self.buffer
		try:
			self.connection.connect(('whois.cymru.com',43))
		except:
			print "[*] Communication Error"
			sys.exit(1)
		self.connection.send(self.buffer)
		self.reply = self.myrecv()
		self.reply = cStringIO.StringIO(self.reply)
		self.reply = self.reply.readlines()
		for self.item in self.reply[1:]:
			self.data = self.item.split('|')
			self.origin_AS  = self.data[0].strip()
			self.IP  = self.data[1].strip()
			self.BGP_prefix = self.data[2].strip()
			self.CC = self.data[3].strip()
			self.Registry = self.data[4].strip()
			self.Allocated = self.data[5].strip()
			self.info = self.data[6].strip()
			self.AS_name = self.data[7].strip()
			print """
Query: %s
Origin AS: %s
IP: %s
BGP_prefix: %s
CC: %s
Registr: %s
Allocated: %s
AS_name: %s""" % (self.info, self.origin_AS,self.IP,self.BGP_prefix,self.CC,self.Registry,self.Allocated,self.AS_name)
			if b:
				self.sql_populate(b)
			else:
				self.sql_populate()
		self.conn.close()

        def add_email(self,email):

                self.email = email
                self.sql_conn()
                self.cur = self.conn.cursor()
                self.cur.execute("insert into emails (email) values (%s)", self.email)
                self.conn.commit()
                print "[*] Adding Email %s to table\r\n" % self.email
                self.cur.close()
                self.conn.close()

        def add_ip(self,network):
                
                self.network = network
                self.sql_conn()
                self.cur = self.conn.cursor()
                self.cur.execute("insert into watched (network) values (%s)",self.network)
                self.conn.commit()
                print "[*] Adding IP %s to table\r\n" % self.network
                self.cur.close()
                self.conn.close()

	def reccmp(self,rec1,rec2):
	
		self.rec1 = rec1
                self.rec2 = rec2
                if self.rec1 == self.rec2:
			return True
		else:
			return False
			
        def send_email(self,msg):
                
                self.msg = MIMEText(msg)
                self.sql_conn()
                self.cur = self.conn.cursor()
                self.to = []
                self.cur.execute("select email from emails")
                self.emails = self.cur.fetchall()
                for self.mail in self.emails:
                        self.to.append(self.mail[0])
                self.from_email = 'bgp-mon@alert-moi.com'
                self.msg['subject'] = 'ISC BGP hijack  monitor Alert'
                self.server = smtplib.SMTP('localhost',25)
                #self.server.set_debuglevel(True)
                self.server.starttls()
                self.server.sendmail(self.from_email,self.to,self.msg.as_string())
                self.server.quit()


	def checking(self):
		self.msg = ""	
		self.sql_conn()
		self.cur = self.conn.cursor()
		self.cur2 = self.conn.cursor()
		self.cur3 = self.conn.cursor()
		self.cur.execute('select network,Origin_AS,IP,BGP_prefix,CC,Registry,Allocated,AS_Name from base_line')
		for self.row in self.cur:
			self.network_BL,self.Origin_AS_BL, self.IP_BL, self.BGP_prefix_BL,self.CC_BL,self.Registry_BL,self.Allocated_BL,self.AS_Name_BL = self.row
			self.cur2.execute('select MAX(time_stamp) from latest_update where network = %s', (self.network_BL))
			self.ts = self.cur2.fetchone()
			self.cur2.execute('select network,Origin_AS,IP,BGP_prefix,CC,Registry,Allocated,AS_Name from latest_update where network = %s and time_stamp = %s', (self.network_BL, self.ts[0]))
			self.row_latest = self.cur2.fetchone()
			self.network_LU,self.Origin_AS_LU, self.IP_LU, self.BGP_prefix_LU,self.CC_LU,self.Registry_LU,self.Allocated_LU,self.AS_Name_LU = self.row_latest		
			self.diff = False		
			if not self.reccmp(self.Origin_AS_BL,self.Origin_AS_LU):
				self.diff = True
				self.dtype = 'Origin_AS'
				self.diff_rec = self.Origin_AS_LU	
			elif not self.reccmp(self.IP_BL, self.IP_LU):
				self.diff = True
				self.dtype = 'IP'
				self.diff_rec = self.IP.LU
			elif not self.reccmp(self.BGP_prefix_BL, self.BGP_prefix_LU):
				self.diff = True
				self.dtype = 'BGP_prefix'
				self.diff_rec = self.BGP_prefix_LU
			elif not self.reccmp(self.CC_BL, self.CC_LU):
				self.diff = True
				self.dtype = 'CC'
				self.diff_rec = self.CC_LU
			elif not self.reccmp(self.Registry_BL, self.Registry_LU):
				self.diff = True
				self.dtype = 'Registry'
				self.diff_rec = self.Registry_LU
			elif not self.reccmp(self.Allocated_BL, self.Allocated_LU):
				self.diff = True
				self.dtype = 'Allocated'
				self.diff_rec = self.Allocated_LU
			elif not self.reccmp(self.AS_Name_BL, self.AS_Name_LU):
				self.diff = True
				self.dtype = 'AS_Name'
				self.diff_rec = self.AS_Name_LU
			else:	
				print "--------Network:%s----------\r\n" % self.network_LU
				print "[*} Orginating ASN is in baseline: %s" % self.Origin_AS_LU
				print "[*] Requested IP address is in baseline: %s" % self.IP_LU
				print "[*] Announced BGP network Prefix is in baseline: %s" % self.BGP_prefix_LU
				print "[*] Country Code is in baseline: %s" % self.CC_LU
				print "[*] Network Registry is in baseline: %s" % self.Registry_LU
				print "[*] Date of Allocation is in baseline: %s" % self.Allocated_LU
				print "[*] AS Name is in baseline: %s\r\n\r\n" % self.AS_Name_LU

			if self.diff:
			
				self.msg = """
-------- Different Entry: %s ------ Network: %s ---------
[*] Error Matching Record to Baseline
[*] Latest Record: Origin ASN %s, Baseline: Origin ASN %s
[*] Latest Record: IP %s, Baseline: IP %s
[*] Latest Record: BGP Prefix %s, Baseline: BGP Prefix %s
[*] Latest Record: CounrtyCode %s, Baseline: CountryCode %s
[*] Latest Record: Registry %s, Baseline: Registry %s
[*] Latest Record: Allocation %s, Baseline: Allocation %s
[*] Latest Record: AS Name %s, Baseline: AS Name %s\r\n\r\n""" % (self.rec2, self.network_BL, self.Origin_AS_LU, self.Origin_AS_BL, self.IP_LU, self.IP_LU, self.BGP_prefix_LU, self.BGP_prefix_BL, self.CC_LU, self.CC_BL, self.Registry_LU, self.Registry_BL, self.Allocated_LU, self.Allocated_LU, self.AS_Name_LU, self.AS_Name_BL)
			#	self.send_email(self.msg)
				self.done =  False
				self.cur3.execute("select %s,network from latest_update where network=%%s and time_stamp != %%s" % self.dtype, (self.network_LU,self.ts[0]))
				for self.r in self.cur3:
					self.check, self.hack = self.r
					if self.reccmp(self.check,self.diff_rec):
						self.done = True
				if self.done:
					self.cur3.execute("select network,diff_type,diff_rec from validate where network=(select network from watched where id=%s) and diff_type=%s and diff_rec=%s", (self.network_LU, self.dtype, self.diff_rec))
					if self.cur3.fetchone() == None:
						self.cur3.execute("insert into validate (network,diff_type,diff_rec) values ((select network from watched where id =%s),%s,%s)", (self.network_LU, self.dtype, self.diff_rec))
						self.conn.commit()
						print "[*] Differene already alerted Adding New %s Record to validation table: %s" % (self.dtype,self.diff_rec)
					else:
						print "[*] Item Already in Validation Table"
				else:
					print "Aleeeeeeeeeeeeeeerrrrrrrrrrrt!!!!"
					print self.msg
					self.send_email(self.msg)
		self.conn.close()	
		self.cur.close()
		self.cur2.close()
		self.cur3.close()

	def validate(self,d=None):
	
		self.answer = False
		self.sql_conn()
		self.cur = self.conn.cursor()
	
		if d:
			self.d = d
			self.cur.execute("select id,network, diff_type, diff_rec from validate where network = (select id from watched where netowrk = %s)", self.d)
			print "[*] Gathering Entries that need validation from database for domain: %s" % self.d
		else:
			self.cur.execute("select id,network,diff_type,diff_rec from validate")
			print "[*] Gathering Entries that need validation for all QUERIES"
	
		if not self.cur.fetchone():
			print "[*] No Entries Found for specified query"
		else:
			for self.r in self.cur:
	
				self.id_v,self.network_v, self.dtype_v, self.diff_rec_v = self.r
				self.cur.execute("select network from watched where id = %s", self.network_v)
				self.d = self.cur.fetchone()[0]
				print "[*] Entry for network %s Different Record %s for Type %s" % (self.d, self.diff_rec_v, self.dtype_v)
				print "[*] please enter choice [Y]Yes, [N]No"
				self.question = raw_input("Validate Entry? ")
				while not self.answer:
					if self.question == 'Y':
		
						self.cur.execute("update baseline set %s=case when %s is null then %%s when %s like %%s then %%s else concat_ws(',',%s,%%s) end,time_stamp=now() where netowrk=%s" % (self.dtype_v, self.dtype_v, self.dtype_v, self.dtype_v), (self.diff_rec_v, self.diff_rec_v, self.diff_rec_v, self.diff_rec_v, self.network_v))
		
						self.cur.execute("delete from validate where id = %s", self.id_v)
						print "[*] Malicious Entry Validated"
						print "[*] New Entry Added to Baseline."	
						self.answer = True

					elif self.question == 'N':
						self.cur.execute("insert into alert_history(network,diff_type,diff_rec) values (%s,%s,%s)", (self.d, self.dtype_v, self.diff_rec_v))
						self.cur.execute("delete from validate where id = %s", self.id_v)
						self.answer = True
						self.msg_v = """
Maliciouss entry found after validation for:
[*] Domain: %s	
[*] Query Type: %s
[*] Malicious Entry: %s""" % (self.d,  self.dtype_v, self.diff_rec_v)
						print self.msg_v
						self.send_email(self.msg)
					else:
						print "[*] Invalid Choicei,Try again"
	
					self.conn.commit()
					self.cur.close()
			
parser  = argparse.ArgumentParser(description = 'BGP Hikack Monitoring', epilog = 'Saif El-Sherei')
parser.add_argument('-b','--baseline',help = 'Baseline records',action = 'store_true')
parser.add_argument('-c','--check',help = 'Check for any discrepancies in database',action='store_true')
parser.add_argument('-e','--email',help = 'Add Email to database')
parser.add_argument('-ip','--ip',help = 'Add IP to database')
p = parser.parse_args()
c  = start()

if p.baseline and not p.check and not p.email and not p.ip:

	c.magic(p.baseline)

if not p.baseline and not p.check and not p.email and not p.ip:
	
	c.magic()	
	c.checking()	

if p.check and not p.baseline and not p.email and not p.ip:
	
	c.checking()

if p.email and not p.baseline and not p.check and not p.ip:

	c.add_email(p.email)

if p.ip and not p.baseline and not p.check and not p.email:

	c.add_ip(p.ip)
	c.magic(p.baseline)


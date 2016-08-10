#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sqlite3
import urllib2
import time
import datetime
import re
import os
import sys
import pyowm
import math
from BME280 import *
from Adafruit_CharLCD import Adafruit_CharLCD

#========================================
# Settings
#========================================
home_dir = "/home/pi/weather/"
www_dir = "/var/www/html/"
delete_data_older_than_days = 30
temperature_unit = 'C' # 'C' | 'F'
pressure_unit = 'mm Hg' # 'Pa' | 'mm Hg'
humidity_unit = '%'
clouds_unit = '%'

#========================================
sea_level = 110 # meters

#========================================
database_name = 'weather.db'
owm_temperature_field = 'owm_temperature'
owm_pressure_field =    'owm_pressure'
owm_pressureOSL_field = 'owm_pressureOSL'
owm_humidity_field = 'owm_humidity'
owm_dewpoint_field = 'owm_dewpoint'
owm_clouds_field = 'owm_clouds'
real1_temperature_field = 'real1_temperature'
real1_pressure_field =    'real1_pressure'
real1_pressureOSL_field = 'real1_pressureOSL'
real1_humidity_field = 'real1_humidity'
real1_dewpoint_field = 'real1_dewpoint'

units = {owm_temperature_field: temperature_unit,
 	owm_pressure_field: pressure_unit,
 	owm_pressureOSL_field: pressure_unit,
	owm_humidity_field: humidity_unit,
 	owm_dewpoint_field: temperature_unit,
	owm_clouds_field: clouds_unit,
	
	real1_temperature_field: temperature_unit,
 	real1_pressure_field: pressure_unit,
 	real1_pressureOSL_field: pressure_unit,
	real1_humidity_field: humidity_unit,
 	real1_dewpoint_field: temperature_unit,
	
}

def convert(value, unit):
	if unit == 'F':
		# Convert from Celsius to Fahrenheit
		return round(1.8 * value + 32.0, 2)
	if unit == 'mm Hg':
		 #Convert from Pa to mm Hg
		return round(value * 0.00750061683, 2)
	return value

def calc_dew_point(T, RH):
	a = 6.112 # millibar
	b = 18.729 # 
	c = 257.87 # *Celsius
	d = 227.3  # *Celsius
	#print "T=",T,"RH=",RH
	#print "log(",RH/100.0,")=",math.log(RH/100.0)
	gamma = math.log(RH/100.0*math.exp((b-T/d)*T/(T+c)))	
	return c*gamma/(b-gamma)

def calc_pressure_sea_level(P1, T):
	M = 0.029 # 
	g = 9.81 # 
	R = 8.31 # 
	#d = 227.3  # *Celsius
	P0 = P1/math.exp(-M*g*sea_level/(R*(273+T)))
	#print "P1 = ",P1,"P0 = ",P0 ,"hPa"
	return P0


def get_chart_data(field, days):
	global units
	result = ""
	start_time =  time.time() - 86400*days
	SQL = "SELECT id, {0} FROM weather WHERE (id > {1}) ORDER BY id DESC".format(field, start_time)
	cur.execute(SQL)
	for row in cur:
		value = convert(row[1], units[field])
		result += "[new Date({0}), {1}], ".format(int(row[0]*1000), value)
	result = re.sub(r', $', '', result)
	return result

def get_chart_data_temperature(days):
	global units
	result = ""
	start_time =  time.time() - 86400*days
	SQL = "SELECT id, {0}, {1} FROM weather WHERE (id > {2}) ORDER BY id DESC".format(temperature_field, dew_point_field, start_time)
	cur.execute(SQL)
	for row in cur:
		temperature = convert(row[1], temperature_unit)
		dew_point = convert(row[2], temperature_unit)
	
		result += "[new Date({0}), {1}, {2}], ".format(int(row[0]*1000), temperature, dew_point)
	result = re.sub(r', $', '', result)
	return result



#Read data from Sensor
ps = BME280()
ps_data = ps.get_data()
real1_temperature=ps_data['t']
real1_pressure=ps_data['p']
real1_humidity=ps_data['h']
#dew point
real1_dewpoint = calc_dew_point(real1_temperature,real1_humidity) 
#pressure on sea level
real1_pressureOSL=calc_pressure_sea_level(real1_pressure,real1_temperature)

print "###Real###"
print "Temperature :", convert(real1_temperature, units[real1_temperature_field])," "+units[real1_temperature_field]
print "Pressure:", convert(real1_pressure, units[real1_pressure_field]), units[real1_pressure_field]
print "Humidity:", real1_humidity, units[real1_humidity_field]
print "dewpoint = ",real1_dewpoint 
print "pressure_on_sea_level = ", real1_pressureOSL



f = open(home_dir+'appid','r')
owm_appid = f.read()
owm_appid = owm_appid.rstrip('\n')
f.close()
#print owm_appid

owm = pyowm.OWM(owm_appid) 

observation = owm.weather_at_place("Kramatorsk")
w = observation.get_weather()
owm_temperature=w.get_temperature('celsius')['temp']
owm_humidity=w.get_humidity()
owm_clouds=w.get_clouds()
owm_pressure=w.get_pressure()['press']*100;
owm_pressureOSL=w.get_pressure()['sea_level']*100;
#dew point
owm_dewpoint = calc_dew_point(owm_temperature,owm_humidity) 
#owm_dewpoint = w.get_dewpoint() #dont work


print "###OWM###"
print "Temperature:", convert(owm_temperature, units[owm_temperature_field]), "�"+units[owm_temperature_field] 
print "Pressure:", convert(owm_pressure, units[owm_pressure_field]), units[owm_pressure_field] 
print "Humidity:", owm_humidity, units[owm_humidity_field]

print "dewpoint = ",owm_dewpoint 
print "pressure_on_sea_level = ", owm_pressureOSL



#LCD
#lcd = Adafruit_CharLCD()
#lcd.clear()
#lcd.home()
#lcd.message('T=%s  P=%s\n' % (convert(ps_data['t'], units[temperature_field]), convert(ps_data['p'], units[pressure_field])))
#lcd.message('H=%s%%' % (ps_data['h']))

# ESPEAK
#speak_str = "Тем пе ратура "
#if ps_data['t'] < 0:
#	speak_str += "минус"
#speak_str += str(int(round(abs(ps_data['t']))))
#os.system('espeak "' + speak_str + '" -vru -s50 -a100 2> /dev/null')

#Connect to database
con = sqlite3.connect(home_dir + database_name)
cur = con.cursor()

#Cheak actual time

SQL="SELECT MAX(id) FROM weather"
cur.execute(SQL)
last = cur.fetchone()[0]
now = time.time()
print "Last time: "+str(last)
print "Time now:  "+str(now)

if now<last:
	con.close
	f=open('log','a') #a=append
	f.write("ERROR: Time not sync\n")
	f.close
	sys.exit() 
	

#Insert new reccord
SQL="INSERT INTO weather VALUES({0}, {1}, {2}, {3} ,{4}, {5}, {6}, {7}, {8} ,{9}, {10}, {11})".format(
time.time(),
owm_temperature,
owm_pressure,
owm_pressureOSL,
owm_humidity,
owm_dewpoint,
owm_clouds,
real1_temperature,
real1_humidity,
real1_pressure,
real1_pressureOSL,
real1_dewpoint)
cur.execute(SQL)
con.commit()

#Delete data older than 30 days
start_time =  time.time() - 86400 * delete_data_older_than_days
SQL = "DELETE FROM weather WHERE (id < {0})".format(start_time)
cur.execute(SQL)
con.commit()

#Read template & make index.htm
f = open(home_dir+'templates/index.tpl', 'r')
txt = f.read()
f.close()

#Prepare html
date_time = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M')

#Units
txt = re.sub('{temperature_unit}', units[temperature_field], txt)
txt = re.sub('{pressure_unit}', units[pressure_field], txt)
txt = re.sub('{humidity_unit}', units[humidity_field], txt)

#Current data
txt = re.sub('{time}', date_time, txt)
txt = re.sub('{temperature}', str(convert(ps_data['t'], units[temperature_field])), txt)
txt = re.sub('{pressure}', 'P1 = '+str(convert(ps_data['p'], units[pressure_field]))+' P0 = '+
                           str(convert(Pressure_on_sea_level, units[pressure_field])), txt)
txt = re.sub('{humidity}', str(ps_data['h']), txt)
txt = re.sub('{dew_point}', str(convert(dew_point,units[temperature_field])), txt)

#Day ago
txt = re.sub('{temperature24h}', get_chart_data_temperature(1), txt)
txt = re.sub('{pressure24h}', get_chart_data(pressure_field, 1), txt)
txt = re.sub('{humidity24h}', get_chart_data(humidity_field, 1), txt)
txt = re.sub('{dew_point24h}', get_chart_data(dew_point_field, 1), txt)

#Last week
txt = re.sub('{temperature7d}', get_chart_data_temperature(7), txt)
txt = re.sub('{pressure7d}', get_chart_data(pressure_field, 7), txt)
txt = re.sub('{humidity7d}', get_chart_data(humidity_field, 7), txt)

#Writing file index.htm
f = open(www_dir+'index.html','w')
f.write(txt)
f.close()

#Database connection close
con.close()

#Send data to my site
s="{0}:{1}:0:{2}:".format(int(ps_data['p']), int(ps_data['t']), int(ps_data['h']))
response = urllib2.urlopen("http://avispro.com.ua/getdata.php?data="+s)

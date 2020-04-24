# Cisco Perfmon TIG script
Script to get perfmon stats from CallManager to graph in a TIG stack

### Requirements

* Tested only on Python 3.6+
* zeep
* influxdb
* lxml
* argparse

### Usage

Run from the commandline

```
python3 perfmon_arg.py -ip 10.10.20.1 10.10.20.2 -u administrator -p ciscopsdt -c 'Cisco CallManager'
Starting collection of Perfmon stats
Finishing collecting Perfmon stats
```

### InfluxDB setup
```
$ influx -precision rfc3339
> CREATE DATABASE cisco_perfmon WITH DURATION 90d
> show databases
> use cisco_perfmon
> show measurements
```

### Automate with PM2

Run from the commandline

```
pm2 start perfmon_arg.py --interpreter python3 --name cisco_callmanager --cron '*/5 * * * *' --no-autorestart -- -ip 10.10.20.1 10.10.20.2   -u administrator -p ciscopsdt -c 'Cisco CallManager'
```
### Graph with Grafana
![](https://github.com/sieteunoseis/cisco_perfmon_influxdb/blob/master/images/Grafana1.png)

### Useful PM2 commands

```
$ pm2 [list|ls|status]
$ pm2 flush
$ pm2 log
$ pm2 restart app_name
$ pm2 reload app_name
$ pm2 stop app_name
$ pm2 delete app_name
$ pm2 save or pm2 set pm2:autodump true
$ pm2 stop all
$ pm2 show <id|name>
$ pm2 startup
$ pm2 monit

```
[PM2 Quick Start](https://pm2.keymetrics.io/docs/usage/quick-start/)

### License

MIT

# IntelliAd
Coarsly Measuring memory, CPU, traffic, and battry cost of an apk, and needs more concise measurement of battery costs. This repository also contains ad-related reviews which explictly contains words `ads` or `advert*` using regex.

### Cost Measurement
1. Install RERAN in your rooted mobile phone. Detailed info can be found in this [repository](https://github.com/cuiyungao/RERAN). Then you should use RERAN to record a series of events you want to measure the costs, and save the events to a file, e.g., `./app_path/events.txt`.

2. Run the `cost_measurement.py` file to profile the costs.
```
python cost_measurement.py apk_name device apk_path count fsave_path aapt_path
	apk_name:  name of apk for measurement.
	device:  device_id of your mobile phones, 16-bit number
	apk_path:  path of your apk for measurement
	count:  measurement times. Usually, we take the average measurement results for analysis.
	fsave_path:  path to save the measurement results
	aapt_path:  execution path of aapt.exe, under Android install path:  e.g., .\\Android\\sdk\\build-tools\\25.0.1\\aapt.exe
```

You will find the records of CPU frequency in `*_cpufreq.txt`, real-time thread number in `*_stat.txt`, memory info in `*_top.txt`, and traffic info in `*_dns_log.cap`.

3. Calculate the ad costs of memory/CPU, thread number, traffic, and battery. We save records of with-ads apps under `with_ads` file and no-ads apps under `no_ads` file.
```
python cost_computation.py ad_path no_ad_path time_log_path
	ad_path:  path of recorded costs of with-ads app
	no_ad_path:  path of recorded costs of no-ads app
	time_log_path:  path of corresponding time.log file
```

You will get the cost results in the `./results/cost_dict_new.json`.

### Ad-Related Reviews
You can find ad-related reviews under `ad_reviews`, where `adData` contains attributes of reviews, corresponding to each line of review in the file `adReview`. Totally, 19,579 reviews are used.


This repository part of code for our ICSE-C'17 paper: IntelliAd: assisting mobile app developers in measuring ad costs automatically. https://dl.acm.org/citation.cfm?id=3098430

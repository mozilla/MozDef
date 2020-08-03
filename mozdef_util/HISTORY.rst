=======
History
=======

1.0.0 (2018-10-16)
------------------

* First release on PyPI.


1.0.1 (2018-10-17)
------------------

* Modify License


1.0.2 (2018-10-30)
------------------

Update Geolite db location


1.0.3 (2019-01-16)
------------------

Add is_ip utility function


1.0.4 (2019-01-23)
------------------

* Replaced timer with threads for cleaner bulk importing


1.0.5 (2019-03-06)
------------------

* Replace elasticsearch flush with refresh


1.0.6 (2019-03-29)
------------------

* Add get_aliases function to elasticsearch client


1.0.7 (2019-04-07)
------------------

* Add close_index and open_index functions to elasticsearch client


1.0.8 (2019-04-16)
------------------

* Transition away from custom _type for elasticsearch documents


2.0.0 (2019-06-27)
------------------

* Add support for Elasticsearch 6
* Remove support for Elasticsearch 5


2.0.1 (2019-06-28)
------------------

* Fixed setup.py relative file paths


2.0.2 (2019-06-28)
------------------

* Attempted fix at including static files


2.0.3 (2019-06-28)
------------------

* Fixed static file includes in python package


3.0.0 (2019-07-08)
------------------

* Updated to work with python3
* Removed support for python2


3.0.1 (2019-07-08)
------------------

* Updated bulk queue to acquire lock before saving events


3.0.2 (2019-07-17)
------------------

* Updated ElasticsearchClient.get_indices() to include closed indices


3.0.3 (2019-07-18)
------------------

* Added ElasticsearchClient.get_open_indices()

3.0.4 (2019-09-19)
------------------

* Added SubnetMatch query models

3.0.5 (2020-04-29)
------------------

* Rewrite dict2List to improve correctness and generality

3.0.6 (2020-04-29)
------------------

* Ensure dict2List changes are included

3.0.7 (2020-08-03)
------------------

* Replaces plugin structure in event with mozdef data class structure
* Updates wheel version in requirements.txt
* Adds comments to Make file
* Updates Readme with release instructions

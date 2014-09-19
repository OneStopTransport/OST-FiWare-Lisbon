Here we can find more technical details about the project.

## Organization

There are two applications in this project:

- `fiware` - responsible for fetching mobility data from OST and inserting it into Orion Context Broker. It gets the full GTFS dataset and puts it as JSON models (**CAUTION**: it's obsolete because we've decided to use CKAN instead of Orion);
- `ckan` - this CKAN connector is able to integrate OST's mobility data in two ways, both using OST APIs:
	- fetch GTFS files (CSV as specified by the standard) and push them to the DataStore (CKAN extension), using [another project's capabilities](https://github.com/rjfv/datastore-loader);
	- fetch GTFS Stops located in the Lisbon district, convert them to a specific JSON format (specified by the project's consortium) and push them to CKAN DataStore, using its APIs directly. 

`utils` is not an application, it contains the exceptions, constants and other random stuff needed by the other two apps. Notice that the capability to import GTFS data from CKAN back to OST was also implemented. It's also `ckan` who's responsible for that, although it only serves for demonstration purposes.

---

## Setup

This is a Python project that can be run as [Celery](http://www.celeryproject.org/) workers.

#### Requirements

- **[Python 2.7](https://www.python.org/download/releases/2.7)**
- **[Pip](http://pip.readthedocs.org/en/latest/quickstart.html)**
- **[cURL](http://curl.haxx.se/download.html)**

#### "Should I use a virtual environment?"

**YES**. It's strongly recommended to use a [virtual environment tool](http://en.wikipedia.org/wiki/Virtual_environment_software) to control the libraries' versions. We suggest **[pyenv](https://github.com/yyuu/pyenv)** with **[pyenv-virtualenv](https://github.com/yyuu/pyenv-virtualenv)**, but other solutions may suit you.

#### Installation

After setting that up and creating a `virtualenv` for this project, install its libraries:

```
git clone git@github.com:OneStopTransport/OST-FiWare-Lisbon.git
cd OST-FiWare-Lisbon/
git submodule update --init
pip install -r fiware_lisbon/requirements.pip
```

...and that's it.

---

## Usage

As stated before, this project fetches data from OST and inserts it into a CKAN or Context Broker instance. In order for it to work, we need a CKAN instance or a Context Broker instance running on FI-LAB (or on your server) and a suitable API Key to be used with OST. 

#### Environment Requirements

- [OST](https://www.ost.pt) developer account (Sign up > Login > Settings > Developer Settings) ;
- [OST Server API Key](https://github.com/OneStopTransport/OneStopTransport/wiki/Autenticac%CC%A7a%CC%83o-por-chave);
- [Orion Context Broker](http://catalogue.fi-ware.org/enablers/configuration-manager-orion-context-broker) instance running on FI-LAB with a public IP (check the [documentation](http://catalogue.fi-ware.org/enablers/publishsubscribe-context-broker-orion-context-broker/documentation) for details) or on your custom server;
- [CKAN](http://ckan.org/) instance with [DataStore](http://docs.ckan.org/en/latest/maintaining/datastore.html) extension. We'll try to provide you a Vagrant for easy deployment;
- [CKAN API Key](http://docs.ckan.org/en/latest/api/index.html#authentication-and-api-keys)  which you can retrieve from your profile, after creating an account on the CKAN instance;
- [RabbitMQ](http://www.rabbitmq.com/) instance if you want this being run as a [Celery Beat Worker](http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html).


#### Environment variables

For security reasons, all the confidential data (such as the API Keys or the Context Broker Host) were not added to the project's repository, since they're retrieved from the system's environment. If you'll be running this project in an Unix system, you can put the following lines on the `~/.exports` file or in one of the following: `~/.bash_profile`, `~/.bashrc` or `~/.profile`:

```
# One.Stop.Transport API Keys 
export OST_SERVER_KEY="<INSERT_OST_API_KEY_HERE>"
export FIWARE_HOST="<INSERT_CONTEXTBROKER_IP_HERE>"
export CKAN_API_KEY="<INSERT_CKAN_API_KEY_HERE>"
export CKAN_HOST="<INSERT_CKAN_HOST_HERE>"
```

`FIWARE_HOST` can be an IP address or an URL, but **don't forget** the `http://` protocol and the `1026` port, or else the ContextBroker operations will not work.

If you'll be running this as a [Celery](http://www.celeryproject.org/) worker, you'll need this too:
```
# RabbitMQ credentials and URLs
export MQ_HOST_PROD="messaging.vhost.ost.pt"		# Only if you're running this on the OST architecture
export MQ_HOST_TEST="<INSERT_RABBITMQ_HOST_HERE>"
export MQ_USER="<INSERT_MQ_USER_HERE>"
export MQ_PASSWORD="<INSERT_MQ_PASSWORD_HERE>"
export MQ_VHOST="/"
```

#### Running the project

There are two procedures, one if you'll use this as a regular Python project or as a periodic [Celery Beat worker](http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html).

#### - Regular Python project

Just run the following on the project's directory (`fiware_lisbon`):

```
python -m fiware.tasks	# to import GTFS data to ContextBroker
python -m ckan.tasks	    # to import GTFS data to CKAN
```

#### - Celery Beat 

Just run the following on the project's directory (fi-ware-lisbon):

```
celery worker -B -Q fiware_queue
```

And it will transfer the data at 6:00 AM to the Context Broker and at 6:30 AM to the CKAN DataStore, every day!

---

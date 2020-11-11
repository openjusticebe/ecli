# ECLI case law access provider
This component lists and provides access to Belgian case law, using the European Case Law identifier.

🚧 Under construction 🚧

## Navigation
Based on previous experience with [dpserv](https://github.com/PieterjanMontens/dpserv_client), this component provides navigation acces to belgian case law through a [content-negotiated](https://developer.mozilla.org/en-US/docs/Web/HTTP/Content_negotiation) [HATEOAS](https://fr.wikipedia.org/wiki/HATEOAS) [RESTful](https://en.wikipedia.org/wiki/Representational_state_transfer) interface.

## Local development

You need
- python >= 3.8
- [poetry](https://python-poetry.org/)

### Install
```python
> poetry install
```

### Run
```python
> poetry run api
```

A local config file can be used (toml format) this way:
```python
> poetry run api --config config.toml
```


## Examples
* Api navigation : [https://ecli.openjustice.be](https://ecli.openjustice.be)
* Council of state : [ECLI:BE:RVSCDE:2020:247.760](https://ecli.openjustice.be/ecli/ECLI:BE:RVSCDE:2020:247.760)
* Constitutionnal Court : [ECLI:BE:CC:2020:141](https://ecli.openjustice.be/ecli/ECLI:BE:CC:2020:141)
* Other courts : [ECLI:BE:CTLIE:2017:ARR.20170718.3](https://ecli.openjustice.be/ecli/ECLI:BE:CTLIE:2017:ARR.20170718.3)

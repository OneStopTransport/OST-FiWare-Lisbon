#!/usr/bin/env python
# encoding: utf-8
class APIKeyError(Exception):
    def __str__(self):
        return 'APIKeyError'

class CrawlerError(Exception):
    def __str__(self):
        return 'CrawlerError'

class OSTError(Exception):
    def __str__(self):
        return 'OSTError'
    
class FiWareError(Exception):
    def __str__(self):
        return 'FiWareError'
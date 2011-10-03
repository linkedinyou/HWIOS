# -*- coding: utf-8 -*-
"""
    services.web_ui.models.signal
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Simple observer/subscriber classes for events in HWIOS

    :copyright: Copyright 2011-2012 OS-Networks
    :license: LGPL, See LICENSE for details.
"""

import re


class Signal(object):
    
    
    def __init__(self, name):
        self.name = name
        self.callees = []
        
        
    def register_callee(self, callee_function, filters = None):
        if filters != None: 
            _filter = []
            for filter in filters:
                _filter.append((re.compile(filter[0]), filter[1]))
            filters = _filter
        self.callees.append({'callee':callee_function,'filters':filters})
        
        
    def execute(self, filters = None, **kwargs):
        """Matches available filters against callee filter options. Uses registered filter order """
        for callee in self.callees:
            if filters != None:
                match = 0
                for idx,compiled_filter in enumerate(callee['filters']):
                    rp = compiled_filter[0].match(filters[idx]) 
                    if rp != None and compiled_filter[1] == True:
                        match += 1
                    if rp == None and compiled_filter[1] == False:
                        match += 1
                if match == len(filters):
                    callee['callee'](**kwargs)
            else:
                callee['callee'](**kwargs)
                
                
class SignalPool(object):
    
    def __init__(self, signals = None):
        self.signals = []
        if signals != None:
            self.signals = signals
            
            
    def append(self, signal):
        '''General signal adding'''
        self.signals.append(signal)
        
        
    def remove(self, signal):
        for index, _signal in enumerate(self.signals):
            if _signal == signal:
                self.signal.remove(signal)
                
                
    def send(self, signal_name, filters = None, **kwargs):
        for _signal in self.signals:
            if _signal.name == signal_name:
                _signal.execute(filters = filters,**kwargs)
                
    
    def subscribe(self, signal_name, function, filters = None):  
        '''signal registration, with option filter'''
        for _signal in self.signals:
            if _signal.name == signal_name:
                _signal.register_callee(function, filters)    
    
        
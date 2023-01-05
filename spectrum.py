#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Dec  1 18:23:40 2022

@author: alankar
"""

import numpy as np
import h5py
from itertools import product
import os
import subprocess

warn = False 

class EmissionSpectrum:
    
    def __init__(self):    
        '''
        Prepares the location to read data for generating emisson spectrum.

        Returns
        -------
        None.

        '''
        _tmp = subprocess.check_output('pwd').decode("utf-8").split('/')[1:]
        _pos = None
        for i, val in enumerate(_tmp):
            if val == 'AstroPlasma':
                _pos = i
        _tmp = os.path.join('/',*_tmp[:_pos+1], 'misc', 'cloudy-data', 'emission')
        self.loc = _tmp #'./cloudy-data/emission'
        
        data = h5py.File('%s/emission.b_%06d.h5'%(self.loc,0), 'r')
        self.nH_data   = np.array(data['params/nH'])
        self.T_data   = np.array(data['params/temperature'])
        self.Z_data   = np.array(data['params/metallicity'])
        self.red_data = np.array(data['params/redshift'])
        self.energy   = np.array(data['output/energy'])
        
        self.batch_size = np.prod(np.array(data['header/batch_dim']))
        self.total_size = np.prod(np.array(data['header/total_size']))
        data.close()
    
    def interpolate(self, nH=1.2e-4, temperature=2.7e6, metallicity=0.5, redshift=0.2, mode='PIE'):
        '''
        Interpolate emission spectrum from pre-computed Cloudy table.

        Parameters
        ----------
        nH : float, optional
            Hydrogen number density (all hydrogen both neutral and ionized. The default is 1.2e-4.
        temperature : float, optional
            Plasma temperature. The default is 2.7e6.
        metallicity : float, optional
            Plasma metallicity with respect to solar. The default is 0.5.
        redshift : float, optional
            Cosmological redshift of the universe. The default is 0.2.
        mode : str, optional
            ionization condition either CIE (collisional) or PIE (photo). The default is 'PIE'.

        Returns
        -------
        spectrum : numpy array 2d
            returns the emitted spectrum as a 2d numpy array with two columns.
            Column 0: Energy in keV
            Column 1: spectral energy distribution (emissivity): 4*pi*nu*j_nu (Unit: erg cm^-3 s^-1)

        '''
        
        i_vals, j_vals, k_vals, l_vals = None, None, None, None
        if (np.sum(nH==self.nH_data)==1): 
            i_vals = [np.where(nH==self.nH_data)[0][0], np.where(nH==self.nH_data)[0][0]]
        else:
            i_vals = [np.sum(nH>self.nH_data)-1,np.sum(nH>self.nH_data)]
        
        if (np.sum(temperature==self.T_data)==1): 
            j_vals = [np.where(temperature==self.T_data)[0][0], np.where(temperature==self.T_data)[0][0]]
        else:
            j_vals = [np.sum(temperature>self.T_data)-1,np.sum(temperature>self.T_data)]
        
        if (np.sum(metallicity==self.Z_data)==1): 
            k_vals = [np.where(metallicity==self.Z_data)[0][0], np.where(metallicity==self.Z_data)[0][0]]
        else:
            k_vals = [np.sum(metallicity>self.Z_data)-1,np.sum(metallicity>self.Z_data)]
        
        if (np.sum(redshift==self.red_data)==1): 
            l_vals = [np.where(redshift==self.red_data)[0][0], np.where(redshift==self.red_data)[0][0]]
        else:
            l_vals = [np.sum(redshift>self.red_data)-1,np.sum(redshift>self.red_data)]
            
        spectrum = np.zeros((self.energy.shape[0],2))
        spectrum[:,0] = self.energy
        
        inv_weight = 0
        #print(i_vals, j_vals, k_vals, l_vals)
        
        batch_ids = []
        #identify unique batches
        for i, j, k, l in product(i_vals, j_vals, k_vals, l_vals):
            if (i==self.nH_data.shape[0]): 
                if (warn): print("Problem: nH", nH)
                i = i-1
            if (i==-1): 
                if (warn): print("Problem: nH", nH)
                i = i+1
            if (j==self.T_data.shape[0]): 
                if (warn): print("Problem: T", temperature)
                j = j-1
            if (j==-1): 
                if (warn): print("Problem: T", temperature)
                j = j+1
            if (k==self.Z_data.shape[0]): 
                if (warn): print("Problem: met", metallicity)
                k = k-1
            if (k==-1): 
                if (warn): print("Problem: met", metallicity)
                k = k+1
            if (l==self.red_data.shape[0]): 
                if (warn): print("Problem: red", redshift)
                l = l-1
            if (l==-1): 
                if (warn): print("Problem: red", redshift)
                l = l+1
            counter = (l)*self.Z_data.shape[0]*self.T_data.shape[0]*self.nH_data.shape[0]+ \
                      (k)*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (j)*self.nH_data.shape[0] + \
                      (i)
            batch_id  = counter//self.batch_size 
            batch_ids.append(batch_id)
        batch_ids = set(batch_ids)
        #print("Batches involved: ", batch_ids)
        data = []
        for batch_id in batch_ids:
            hdf = h5py.File('%s/emission.b_%06d.h5'%(self.loc,batch_id), 'r')
            data.append([batch_id, hdf])
        
        for i, j, k, l in product(i_vals, j_vals, k_vals, l_vals):
            if (i==self.nH_data.shape[0]): 
                if (warn): print("Problem: nH", nH)
                i = i-1
            if (i==-1): 
                if (warn): print("Problem: nH", nH)
                i = i+1
            if (j==self.T_data.shape[0]): 
                if (warn): print("Problem: T", temperature)
                j = j-1
            if (j==-1): 
                if (warn): print("Problem: T", temperature)
                j = j+1
            if (k==self.Z_data.shape[0]): 
                if (warn): print("Problem: met", metallicity)
                k = k-1
            if (k==-1): 
                if (warn): print("Problem: met", metallicity)
                k = k+1
            if (l==self.red_data.shape[0]): 
                if (warn): print("Problem: red", redshift)
                l = l-1
            if (l==-1): 
                if (warn): print("Problem: red", redshift)
                l = l+1
                
            d_i = np.abs(self.nH_data[i]-nH)
            d_j = np.abs(self.T_data[j]-temperature)
            d_k = np.abs(self.Z_data[k]-metallicity)
            d_l = np.abs(self.red_data[l]-redshift)
            
            #print('Data vals: ', self.nH_data[i], self.T_data[j], self.Z_data[k], self.red_data[l] )
            #print(i, j, k, l)
            epsilon = 1e-6
            weight = np.sqrt(d_i**2 + d_j**2 + d_k**2 + d_l**2 + epsilon)
            
            counter = (l)*self.Z_data.shape[0]*self.T_data.shape[0]*self.nH_data.shape[0]+ \
                      (k)*self.T_data.shape[0]*self.nH_data.shape[0] + \
                      (j)*self.nH_data.shape[0] + \
                      (i)
            batch_id  = counter//self.batch_size 
            
            for id_data in data:
                if id_data[0] == batch_id:
                    hdf = id_data[1]
                    local_pos = counter%self.batch_size - 1
                    spectrum[:,1] += (np.array(hdf[f'output/emission/{mode}/total'])[local_pos,:]) / weight
                
            inv_weight += 1/weight
         
        spectrum[:,1] = spectrum[:,1]/inv_weight
        
        for id_data in data:
            id_data[1].close()
        
        #array starts from 0 but ion from 1            
        return spectrum 
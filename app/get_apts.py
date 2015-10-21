# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd 
def get_apts(burr, mprce, pdf):
	oo = np.where(pdf.price < mprce)
	sub = pdf.ix[oo[0],:]
	aa = sub.sort(['scores'], ascending=[True])		
	return(result)

	print 'The population is %i' % population
	result = population/1000000.0
	if fromUser != 'Default':
		return result
	else:
		return 'check your input'
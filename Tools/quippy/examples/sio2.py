from quippy import *
from math import ceil
import time
#from pylab import *
from StringIO import StringIO

def alpha_quartz(a=4.9134,c=5.4052, x1=0.4699, x2=0.4141, y2=0.2681, z2=0.7854):
   """Primitive 9-atom orthorhombic alpha quartz cell"""

   a1 = farray((0.5*a, -0.5*sqrt(3.0)*a, 0.0))
   a2 = farray((0.5*a,  0.5*sqrt(3.0)*a, 0.0))
   a3 = farray((0.0,    0.0,             c))

   lattice = fzeros((3,3))
   lattice[:,1] = a1
   lattice[:,2] = a2
   lattice[:,3] = a3
   
   at = Atoms(n=9,lattice=lattice)

   at.set_atoms((14,14,14,8,8,8,8,8,8))

   at.pos[:,1] =  x1*a1 + 2.0/3.0*a3
   at.pos[:,2] =  x1*a2 + 1.0/3.0*a3
   at.pos[:,3] = -x1*a1 - x1*a2
   at.pos[:,4] =  x2*a1 + y2*a2 + z2*a3
   at.pos[:,5] = -y2*a1 + (x2-y2)*a2  + (2.0/3.0 + z2)*a3
   at.pos[:,6] = (y2-x2)*a1 - x2*a2   + (1.0/3.0 + z2)*a3
   at.pos[:,7] = y2*a1 + x2*a2 - z2*a3
   at.pos[:,8] = -x2*a1 + (y2-x2)*a2 + (2.0/3.0 - z2)*a3
   at.pos[:,9] = (x2 - y2)*a1 - y2*a2 + (1.0/3.0 - z2)*a3
   
   return at

def alpha_quartz_cubic(*args, **kwargs):
   """Non-primitive 18-atom cubic quartz cell."""
   a0 = alpha_quartz(*args, **kwargs)
   at = supercell(a0, 4, 4, 1)
   at.map_into_cell()

   lattice = fzeros((3,3))
   lattice[1,1] = a0.lattice[1,1]*2.0
   lattice[2,2] = a0.lattice[2,2]*2.0
   lattice[3,3] = a0.lattice[3,3]

   g = linalg.inv(lattice)
   t = dot(g, at.pos)
   cubic = at.select(logical_and(t >= -0.5, t < 0.5).all(axis=1))
   cubic.set_lattice(lattice)
   return cubic

def beta_quartz():
   pass

def bracket(func, x1, x2, max_iter=50, factor=1.6, **kwargs):
   f1 = func(x1, **kwargs)
   f2 = func(x2, **kwargs)
   for j in range(max_iter):
      if f1*f2 < 0.0:
         return (x1, x2)
      if abs(f1) < abs(f2):
         x1 += factor*(x1 - x2)
         f1 = func(x1, **kwargs)
      else:
         x2 += factor*(x2 - x1)
         f2 = func(x2, **kwargs)
   raise ValueError('Maximum number of iterations exceeded.')

def bisect(func, x1, x2, err=1e-5, max_iter=50, **kwargs):
   f = func(x1, **kwargs)
   fmid = func(x2, **kwargs)
   if f*fmid >= 0.0:
      raise ValueError("Root not bracketed")

   if f < 0.0:
      dx = x2 - x1
      rtb = x1
   else:
      dx = x1 - x2
      rtb = x2

   for j in range(max_iter):
      xmid = rtb + dx
      dx *= 0.5
      fmid = func(xmid, **kwargs)
      if fmid < 0:
         rtb = xmid
      if abs(dx) < err or fmid == 0.0:
         return rtb
   raise ValueError('Maximum number of iterations exceeded.')   

def newton_raphson(func, dfunc, x1, x2, err=1e-5, max_iter=20, **kwargs):
   x = 0.5*(x1 + x2)
   for j in range(max_iter):
      f = func(x, **kwargs)
      df = dfunc(x, **kwargs)
      dx = f/df
      x = x - dx
      print j, x
      if (x1 - x)*(x - x2) < 0.0:
         raise ValueError('Jumped out of brackets')
      if abs(dx) < err:
         return x
   raise ValueError('Maximum number of iterations exceeded.')

def rcut_func(r, alpha, eps):
   return exp(-alpha*r)/r - eps

def rcut_dfunc(r, alpha, eps):
   return -alpha*exp(-alpha*r)/r - exp(-alpha*r)/r**2

def rcut(alpha, eps=1.0/40.0, min=1.0, max=100.0):
   min, max = bracket(rcut_func, min, max, alpha=alpha, eps=eps)
   return bisect(rcut_func, min, max, alpha=alpha, eps=eps)


def force_test(at, p, dx=1e-4):
   analytic_f = fzeros((3,at.n))
   p.calc(at, f=analytic_f)
   num_f = fzeros((3,at.n))
   ep, em = farray(0.0), farray(0.0)

   for i in frange(at.n):
      for j in (1,2,3):
         ap = at.copy()
         ap.pos[j,i] += dx
         p.calc(ap, e=ep)
         print 'e+', j,i,ep
         ap.pos[j,i] -= 2.0*dx
         p.calc(ap, e=em)
         print 'e-', j,i,em
         num_f[j,i] = -(ep - em)/(2*dx)

   return analytic_f, num_f, analytic_f - num_f


def timing_test():
   times = {}

   alpha = 0.0

   xml = """<ASAP_params cutoff="4.0" n_types="2">
   <per_type_data type="1" atomic_num="8" />
   <per_type_data type="2" atomic_num="14" />
   <params>
   15.9994 28.086
   O Si
   48 24
   .f. 0.0 1.d-9  0.0 1 1 1 %f 21.0 18.0 0.0 0.0 raggio,A_ew,gcut,iesr,rcut
    -1.38257 2.76514
    -------------Alphaij---------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    -------------Bij--------------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    ---------------Cij------------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    -----------------Dij----------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    ---------------Eij------------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    ---------------Nij------------------
    0.0000000E+00   8.0000000E+00
    0.0000000E+00
    ---------Tang-Toennies-------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    ---------Tang-Toennies-------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    ---------Tang-Toennies-------------
    0.0000000E+00   0.0000000E+00
    0.0000000E+00
    ---------------D_ms----------------
    2.4748d-4   1.9033d-3        
   -2.0846d-3    
    ---------------Gamma_ms------------
    12.07092 11.15230
    10.45517
    ----------------R_ms---------------
    7.17005 4.63710
    5.75038
    --------------Polarization---------
    8.89378       0.0d0
    0.70,  60,  1.0000000001E-7 2
    ---------------Bpol----------------
    0.0000000E+00   2.02989      
    0.00000000000
    ---------------Cpol----------------
    0.0000000E+00  -1.50435       
    0.00000000    
    --------Aspherical-Ion-Model-------
    F,  F,  7.,  8.
    -----------Adist-------------------
    0.0000000E+00   2.0170894E+00
    2.4232942E+00
    ---------------Bdist---------------
    0.0000000E+00   7.6306646E+01
    1.5861246E+03
    ---------------Cdist---------------
    0.0000000E+00  -1.2069760E-02
    --------------Ddist----------------
    0.0000000E+00  -4.0995369E-02
    2.2483367E-02
    -------------Sigma1----------------
    0.0000000E+00  -1.4410513E+07
    -------------Sigma2----------------
    0.0000000E+00  -5.1477595E+00
    ------------Sigma3-----------------
    0.0000000E+00   1.1143606E+08
    -------------Sigma4----------------
    0.0000000E+00   7.2089861E+00
    -------------Bu1-------------------
    4.1063828E+12   1.8240403E+02
   -2.7852429E+04
    --------------Alphau1--------------
    7.2970202E+00   2.2221123E+00
    2.9876383E+00
    ---------------Bu2-----------------
   -3.4880044E+13  -2.0079894E+03
    4.0014253E+03
    --------------Alphau2--------------
    7.8085212E+00   3.7185181E+00
    2.4488279E+00
   ***********Spring Constant*********
    1.0 1.0 
    1.0
   ***********Spring Cutoff***********
    3.60 2.30
      3.8
   **********Smoothing***************
   0.0 0.0 .f.
   *************Yukawa***************
   %f 10.0 .t.
   </params>
   </ASAP_params>""" 


   reps = (1, 2, 3, 4, 5, 6)
   alphas = (0.0, 0.05, 0.1, 0.5)

   times = {}
   fvar('e')
   at = alpha_quartz_cubic()
   for rep in reps:
      aa = supercell(at, rep, rep, rep)
      for alpha in alphas:
         p = Potential('IP ASAP', xml % (rcut(alpha), alpha))

         t1 = time.time()
         p.calc(aa, e=e)
         t2 = time.time()

         times[(rep,alpha)] = (aa.n, t2-t1)


   ax = gca()
   ax.set_xscale('log')

   for alpha in alphas:
      x = []
      y = []
      for rep in reps:
         n, t = times[(rep,alpha)]
         x.append(n)
         y.append(t)
      plot(x,y, 'o-')

   legend([r'$\alpha=%.2f$ Bohr$^{-1}$ $R=%.2f$ Bohr' % (a, R) for (a,R) in zip(alphas, vectorize(rcut)(alphas))],2)

#################

logical = lambda x: True if x in (1, True, '1', 'True', 't', 'T', '.t.', '.T') else False
real = lambda s: float(s.replace('d', 'e'))

param_format_traj = [
   [('mass', real, 'nspecies', False)],
   [('species', str, 'nspecies', False)],
   [('nsp', int, 'nspecies', False)],
   [('tewald', logical, 1, False),('raggio', real, 1, False),('a_ew', real, 1, False),('gcut', real, 1, False),('iesr', int, 3, False),('rcut', real, 4, False)],
   [('z', real, 'nspecies-1', False)],
   [('alphaij', real, 'triangle(nspecies)', False)],
   [('bij', real, 'triangle(nspecies)', False)],
   [('cij', real, 'triangle(nspecies)', False)],
   [('dij', real, 'triangle(nspecies)', False)],
   [('eij', real, 'triangle(nspecies)', False)],
   [('nij', real, 'triangle(nspecies)', False)],
   [('b_tt1', real, 'triangle(nspecies)', False)],
   [('b_tt2', real, 'triangle(nspecies)', False)],
   [('b_tt3', real, 'triangle(nspecies)', False)],
   [('d_ms', real, 'triangle(nspecies)', False)],
   [('gamma_ms', real, 'triangle(nspecies)', False)],
   [('r_ms', real, 'triangle(nspecies)', False)],
   [('pol', real, 'nspecies', False)],
   [('betapol', real, 1, False),('maxipol', int, 1, False),('tolpol', real, 1, False), ('pred_order', int, 1, False)],
   [('bpol', real, 'triangle(nspecies)', False)],
   [('cpol', real, 'triangle(nspecies)', False)],
   [('taimsp', logical, 'nspecies', False),('xgmin', real, 1, False),('xgmax', real, 1, False)],
   [('adist',   real, 'triangle(nspecies)', False)],
   [('bdist',   real, 'triangle(nspecies)', False)],
   [('cdist',   real, 'nspecies', False)],
   [('ddist',   real, 'triangle(nspecies)', False)],
   [('sigma1',  real, 'nspecies', False)],
   [('sigma2',  real, 'nspecies', False)],
   [('sigma3',  real, 'nspecies', False)],
   [('sigma4',  real, 'nspecies', False)],
   [('bu1',     real, 'triangle(nspecies)', False)],
   [('alphau1', real, 'triangle(nspecies)', False)],
   [('bu2',     real, 'triangle(nspecies)', False)],
   [('alphau2', real, 'triangle(nspecies)', False)],
   [('c_harm',  real, 'triangle(nspecies)', False)],
   [('rmin', real, 'triangle(nspecies)', False)],
   [('a_s', real, 1, False),('n_s', real, 1, False),('smooth', logical, 1, False)],
   [('yukalpha', real, 1, False),('yuksmoothlength', real, 1, False),('tdip_sr', logical, 1, False)]
   ]


param_format_gen = [
   [('testewald', logical, 1, False), ('time', logical, 1, False), ('tpbc', logical, 1, False), ('tangstrom', logical, 1, False),
    ('trydberg', logical, 1, False), ('tev', logical, 1, False)],
   [('nat', int, 1, False), ('nspecies', int, 1, False), ('npar', int, 1, False)],
   [('ntmin', int, 1, False)],
   [('nts', int ,'ntmin', False)],
   [('filepos', str, 1, False)],
   [('fileforce', str, 1, False)],
   [('filestress', str, 1, False)],
   [('filecel', str, 1, False)],
   [('fileene', str, 1, False)],
   [('testforce', logical, 1, False), ('ngrid', int, 1, False), ('gridmin1', real, 1, False), ('gridmax1', real, 1, False),
    ('gridmin2', real, 1, False), ('gridmax2', real, 1, False), ('isp_tf', int, 1, False)],
   [('tquickpar', logical, 1, False)],
   [('mass', real, 'nspecies', False)],
   [('nsp', int, 'nspecies', False)],
   [('tewald', logical, 1, False),('raggio', real, 1, False),('a_ew', real, 1, False),('gcut', real, 1, False),('iesr', int, 3, False),('rcut', real, 4, False)],
   [('z', real, 'nspecies-1', False), ('tz', logical, 'nspecies-1', False)],
   [('alphaij', real, 'triangle(nspecies)', True)],
   [('bij', real, 'triangle(nspecies)', True)],
   [('cij', real, 'triangle(nspecies)', True)],
   [('dij', real, 'triangle(nspecies)', True)],
   [('eij', real, 'triangle(nspecies)', True)],
   [('nij', real, 'triangle(nspecies)', True)],
   [('b_tt1', real, 'triangle(nspecies)', True)],
   [('b_tt2', real, 'triangle(nspecies)', True)],
   [('b_tt3', real, 'triangle(nspecies)', True)],
   [('d_ms', real, 'triangle(nspecies)', True)],
   [('gamma_ms', real, 'triangle(nspecies)', True)],
   [('r_ms', real, 'triangle(nspecies)', True)],
   [('pol', real, 'nspecies', True)],
   [('betapol', real, 1, False),('maxipol', int, 1, False),('tolpol', real, 1, False)],
   [('bpol', real, 'triangle(nspecies)', True)],
   [('cpol', real, 'triangle(nspecies)', True)],
   [('taimsp', logical, 'nspecies', False),('xgmin', real, 1, False),('xgmax', real, 1, False)],
   [('adist',   real, 'triangle(nspecies)', True)],
   [('bdist',   real, 'triangle(nspecies)', True)],
   [('cdist',   real, 'nspecies', True)],
   [('ddist',   real, 'triangle(nspecies)', True)],
   [('sigma1',  real, 'nspecies', True)],
   [('sigma2',  real, 'nspecies', True)],
   [('sigma3',  real, 'nspecies', True)],
   [('sigma4',  real, 'nspecies', True)],
   [('bu1',     real, 'triangle(nspecies)', True)],
   [('alphau1', real, 'triangle(nspecies)', True)],
   [('bu2',     real, 'triangle(nspecies)', True)],
   [('alphau2', real, 'triangle(nspecies)', True)],
   [('c_harm',  real, 'triangle(nspecies)', True)],
   [('rmin', real, 'triangle(nspecies)', False)],
   [('a_s', real, 1, False),('n_s', real, 1, False),('smooth', logical, 1, False)],
   [('yukalpha', real, 1, False),('yuksmoothlength', real, 1, False),('tdip_sr', logical, 1, False)]
   ]

def triangle(n):
   """Return list of length n which sums to nth triangular number"""
   res = []
   for i in range(1,n+1):
      res.append(i)
   res.reverse()
   return res

def inv_trig(t):
   """Given the nth triangular number t_n, return n by inverting t_n = 1/2 n (n+1)"""
   return int(0.5*(sqrt(1+8*t)-1))

output_converters = {
   (real, 'triangle(nspecies)'): lambda v: '\n'.join(['%E '*n for n in triangle(inv_trig(len(v)))]) % tuple(v),
   int: lambda v: ' '.join(['%d' % x for x in v]),
   real: lambda v: ' '.join(['%f' % x for x in v]),
   logical: lambda v: ' '.join(['.t.' if x else '.f.' for x in v]),
   str: lambda v: ' '.join(v)
   }

type_map = {}
for line in param_format_gen:
   for key, conv, nfields, interleave in line:
      if (key, conv, nfields) in output_converters:
         invconv = output_converters[(key, conv, nfields)]
      elif (conv, nfields) in output_converters:
         invconv = output_converters[(conv, nfields)]
      elif conv in output_converters:
         invconv = output_converters[conv]
      else:
         invconv = lambda s: str(s)
      type_map[key] = (conv, invconv)

def read_traj_gen(format, lines, defaults={}):

   lines = filter(lambda x: not (x.strip().startswith('--') or x.strip().startswith('**') or x.strip().startswith('%%')), lines)

   lengths = [ len(x) for x in format ]

   origlines = lines[:]

   params = defaults.copy()
   fixed = {}
   fixed_order = []
   
   evaldict = defaults.copy()
   evaldict['triangle'] = triangle
   for entries in format:
      n = 0
      gotline = False
      for key, conv, nfields, interleave in entries:
         if isinstance(nfields, str):
            nfields = eval(nfields, evaldict)


         if isinstance(nfields, list) and len(nfields) != 1:
            # multiple lines

            if interleave:
               mylines = lines[:2*len(nfields):2]
               ilines = lines[1:2*len(nfields):2]
               del lines[:2*len(nfields)]
            else:
               mylines = lines[:len(nfields)]
               ilines = ['']*len(mylines)
               del lines[:len(nfields)]
               
            for line, iline, nf in zip(mylines, ilines, nfields):
               fields = line.split()
               values = [conv(x) for x in fields[:nf]]
               if key in params:
                  params[key] = params[key] + values
                  evaldict[key] = params[key] + values
               else:
                  if len(values) == 1: values = values[0]
                  params[key] = values
                  evaldict[key] = values
                  
               if interleave:
                  tfields = iline.split()
                  tvalues = [logical(x) for x in tfields[:nf]]

                  if key in fixed:
                     fixed[key] += tvalues
                  else:
                     fixed_order.append(key)
                     fixed[key] = tvalues
                  
         else:
            # just one line, possibly multiple values per line

            if not gotline:
               line = lines[0]
               del lines[0]
               if interleave:
                  iline = lines[0]
                  del lines[0]
               gotline = True
            
            fields = line.split()
            values = [conv(x) for x in fields[n:n+nfields]]
            if len(values) == 1: values = values[0]
            params[key] = values
            evaldict[key] = values

            if interleave:
               tvalues = [logical(x) for x in iline.split()[n:n+nfields]]

               if key in fixed:
                  fixed[key] += tvalues
               else:
                  fixed_order.append(key)
                  fixed[key] = tvalues
            
            n += nfields

   # special case: tz logical option is on same line as z
   if 'tz' in params:
      fixed['z'] = [params['tz']]
      fixed_order.insert(0,'z')
      del params['tz']

   opt_vars = []
   for var in fixed_order:
      if len(fixed[var]) == 1:
         if fixed[var]: opt_vars.append(var)
      else:
         for i,v in enumerate(fixed[var]):
            if v: opt_vars.append((var, i))

   return params, opt_vars

traj_format_str = """%(mass)s
%(species)s
%(nsp)s
%(tewald)s %(raggio)s %(a_ew)s %(gcut)s %(iesr)s %(rcut)s
%(z)s
-------------Alphaij---------------
%(alphaij)s
-------------Bij--------------------
%(bij)s
---------------Cij------------------
%(cij)s
-----------------Dij----------------
%(dij)s
---------------Eij------------------
%(eij)s
---------------Nij------------------
%(nij)s
---------Tang-Toennies-------------
%(b_tt1)s
---------Tang-Toennies-------------
%(b_tt2)s
---------Tang-Toennies-------------
%(b_tt3)s
---------------D_ms----------------
%(d_ms)s
---------------Gamma_ms------------
%(gamma_ms)s
----------------R_ms---------------
%(r_ms)s
--------------Polarization---------
%(pol)s
%(betapol)s %(maxipol)s %(tolpol)s %(pred_order)s
---------------Bpol----------------
%(bpol)s
---------------Cpol----------------
%(cpol)s
--------Aspherical-Ion-Model-------
%(taimsp)s %(xgmin)s %(xgmax)s
-----------Adist-------------------
%(adist)s
---------------Bdist---------------
%(bdist)s
---------------Cdist---------------
%(cdist)s
--------------Ddist----------------
%(ddist)s
-------------Sigma1----------------
%(sigma1)s
-------------Sigma2----------------
%(sigma2)s
------------Sigma3-----------------
%(sigma3)s
-------------Sigma4----------------
%(sigma4)s
-------------Bu1-------------------
%(bu1)s
--------------Alphau1--------------
%(alphau1)s
---------------Bu2-----------------
%(bu2)s
--------------Alphau2--------------
%(alphau2)s
***********Spring Constant*********
%(c_harm)s
***********Spring Cutoff***********
%(rmin)s
**********Smoothing***************
%(a_s)s %(n_s)s %(smooth)s
*************Yukawa***************
%(yukalpha)s %(yuksmoothlength)s %(tdip_sr)s"""

def param_to_str(format, params):

   out_params = {}
   
   for key in params:
      try:
         len(params[key])
         out_params[key] = type_map[key][1](params[key])
      except TypeError:
         out_params[key] = type_map[key][1]([params[key]])

   return format % out_params


def param_to_xml(params, output, encoding='iso-8859-1'):
   from xml.sax.saxutils import XMLGenerator

   xml = XMLGenerator(output, encoding)
   xml.startDocument()

   xml.startElement('ASAP_params', {'cutoff': ' '.join([str(x) for x in params['rcut']]),
                                    'n_types': str(params['nspecies']),
                                    'betapol': str(params['betapol']),
                                    'maxipol': str(params['maxipol']),
                                    'tolpol': str(params['tolpol']),
                                    'pred_order': str(params['pred_order']),
                                    'yukalpha': str(params['yukalpha']),
                                    'yuksmoothlength': str(params['yuksmoothlength'])})
   ti_tj_to_index = {}
   n = 0
   for ti in range(params['nspecies']):
      for tj in range(params['nspecies']):
         if tj > ti: continue
         ti_tj_to_index[(ti,tj)] = n
         n += 1

   for ti in range(params['nspecies']):
      zi = atomic_number_from_symbol(params['species'][ti])
      xml.startElement('per_type_data', {'type':str(ti+1),
                                         'atomic_num': str(zi),
                                         'pol': str(params['pol'][ti]),
                                         'z': str(params['z'][ti])})
      xml.endElement('per_type_data')
      
      for tj in range(params['nspecies']):
         if tj > ti: continue
         idx = ti_tj_to_index[(ti,tj)]
         zj = atomic_number_from_symbol(params['species'][tj])
         xml.startElement('per_pair_data', {'atnum_i':str(zi),
                                            'atnum_j':str(zj),
                                            'D_ms': str(params['d_ms'][idx]),
                                            'gamma_ms': str(params['gamma_ms'][idx]),
                                            'R_ms': str(params['r_ms'][idx]),
                                            'B_pol': str(params['bpol'][idx]),
                                            'C_pol': str(params['cpol'][idx]),
                                            })
         xml.endElement('per_pair_data')
         
   xml.endElement('ASAP_params')
   xml.endDocument()

def update_vars(params, opt_vars, param_str):
   out_params = params.copy()
   opt_values = [real(x) for x in param_str.split()]

   assert(len(opt_values) == len(opt_vars))

   for var, value in zip(opt_vars, opt_values):
      if isinstance(var, str):
         if var not in out_params: raise ValueError('var %s missing' % var)
         print '%s   %f -> %f' % (var, params[var], value)
         out_params[var] = value
      else:
         key, idx = var
         if key not in out_params: raise ValueError('var %s missing' % key)
         print '%s[%d] %f -> %f' % (key, idx, params[key][idx], value)
         out_params[key][idx] = value

   return out_params



default_params = {'species': ['O', 'Si'],
                  'pred_order': 2}

type_map['species'] = (str, output_converters[str])
type_map['pred_order'] = (int, output_converters[int])


def try_new_params(task='md'):
   params = default_params.copy()
   gen_params, opt_vars = read_traj_gen(param_format_gen, open('gen.in.01').readlines())
   params.update(gen_params)

   print 'opt_vars = ', opt_vars

   params = update_vars(params, opt_vars, open('parameters').read())

   # fix masses
   params['mass'] = [ElementMass[x]/MASSCONVERT for x in params['species']]

   # fix charges
   params['z'] = [params['z'], -2.0*params['z']]

   xml = StringIO()
   param_to_xml(params, xml)

   print xml.getvalue()
   
   p = Potential('IP ASAP', xml.getvalue())

   a = supercell(alpha_quartz_cubic(), 2, 1, 2)
   a.calc_connect()

   e = farray(0.0)
   f = fzeros((3,a.n))
   v = fzeros((3,3))
   dip = fzeros((3,a.n))

   if task == 'md':
      ds = DynamicalSystem(a)
      ds.rescale_velo(300.0)
      ds.zero_momentum()

      traj = ds.run(p, dt=1.0, n_steps=100, save_interval=1, calc_dipoles=True)
      return AtomsList(traj)
   elif task == 'minim':

      mp = MetaPotential('Simple', p)
      cio = CInOutput('minim.xyz', OUTPUT)

      verbosity_push(VERBOSE)
      nsteps = mp.minim(a, 'cg', 1e-3, 100, do_pos=True, do_lat=True, do_print=True,
                        print_cinoutput=cio, calc_force=True, calc_dipoles=True)
      verbosity_pop()

      p.calc(a,e=e,f=f,virial=v, calc_dipoles=True)
      a.add_property('force', 0.0, n_cols=3)
      a.force[:] = f
      a.params['e'] = e

      return a, v

   elif task == 'singlepoint':

      p.print_()
      p.calc(a, calc_energy=True, calc_force=True, calc_dipoles=True)

      return a
      
   else:
      raise ValueError('Unknown task %s' % task)


a = try_new_params(task='minim')


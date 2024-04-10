import argparse

import numpy as np
import matplotlib.pyplot as plt

from siglent_scpi import SDS


plt.rcParams['toolbar'] = 'None'
plt.rcParams['axes.xmargin'] = 0

parser = argparse.ArgumentParser(description='Display FFT and calculate THD for a channel on Siglent SDS1202X-E oscilloscope.',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

parser.add_argument('-c',dest='channel',required=True,type=int,help='channel to display',choices=[1,2])
parser.add_argument('-f0',default=1_000,metavar='FREQ',type=int,help='fundamental frequency (in Hz)')
parser.add_argument('-max_f',default=25_000,metavar='FREQ',type=int,help='maximum frequency to display / use for calculations (in Hz)')
parser.add_argument('-f','--floor',default=-85,type=int,help='minimum level of harmonics (in dBvrms)')
parser.add_argument('-ip',required=True,help='ip address of the oscilloscope')
parser.add_argument('-port',default=5025,type=int,help='port on which the oscilloscope is listening')
parser.add_argument('-t','--title',metavar='NAME',help='plot title')
parser.add_argument('-w','--window',metavar='NAME',help='window title')

args = parser.parse_args()

print('thd.py was called with the following arguments:')
print(' '.join(f'{k}={v}' for k, v in vars(args).items()))
print('')

# channel to sample
ch = args.channel-1

# fundamental frequency from which to calculate the THD
f0 = args.f0

# Max frequency of interest
max_f = args.max_f

# minimum level for harmonics
floor = args.floor

# title of the plot
title = args.title

# window title
window = args.window

# ip address of oscilloscope
ip = args.ip
                    
# port on which the oscilloscope will listen
port = args.port

# create an instance of the oscilloscope connection
print(f'Connecting to oscilloscope at {ip}:{port} ...')
sds = SDS(ip,port)
print('Connected.')

def plot(fig,ax):
    global items

    def to_dBVrms(x):
        return 20*np.log10(x)

    drawn = 0
    
    # thd returns yf in V
    thd,xf,yf,bins = sds.thd(ch,f0,max_f,correct_peaks=True,min_level=floor)
    # transform to dBvrms for the display
    yf_dB = to_dBVrms(np.abs(yf))
    s0 = yf_dB[bins[0]]
    if len(bins) > 1:
        s1 = yf_dB[bins[1]]
        textstr = '\n'.join((r'$THD=%.2f$' % (thd, ) + '%',
                             r'$s_0=%i dB_{V_{rms}}$' % (s0,),
                             r'$s_1=%i dB_c$' % (int(s1-s0),),
                            ))
    else:
        textstr = '\n'.join((r'$THD=%.2f$' % (thd, ) + '%',
                             r'$s_0=%i dB_{V_{rms}}$' % (s0,),
                            ))

    props = dict(boxstyle='round', facecolor='lightgrey', alpha=0.75)

    # place a text box in upper left in axes coords
    item = ax.text(0.4, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            verticalalignment='top', bbox=props)
    items.append(item)
    drawn = drawn + 1

    # plot a x at harmonics, and remember the x's to remove them later
    for p in bins[1:]:
        item = ax.scatter(xf[p]/1000,yf_dB[p],marker='x',color='C2')
        items.append(item)
        drawn = drawn + 1

    # plot a dot at fundamental frequency, and remember the dot to remove it later
    item = ax.scatter(xf[bins[0]]/1000,yf_dB[bins[0]],marker='o',color='C2')
    items.append(item)
    drawn = drawn + 1

    # create plot, and remember the lines to remove them later
    item = ax.plot(xf/1000,yf_dB,color='C2',alpha=0.75,linewidth=1)[0]
    items.append(item)
    drawn = drawn + 1

    # remove oldest of the previous items (if any)
    while len(items)>drawn:
        item = items[0]
        items.remove(item)
        item.remove()

    fig.canvas.draw_idle()
    fig.canvas.start_event_loop(0.01)


quit = False

def on_close(event):
    global quit
    quit = True
    

# to set the matplotlib window title, see: https://stackoverflow.com/questions/38307438/set-matplotlib-default-figure-window-title
print('Creating window ...')
fig, ax = plt.subplots(num=window)
fig.canvas.mpl_connect('close_event', on_close)
if title is None:
    title = f'FFT Channel {int(ch+1)}'
plt.title(title)
plt.tight_layout(pad=4)
plt.xlabel('frequency (kHz)')
plt.ylabel(r'$dB_{V_{rms}}$')
plt.show(block=False)
plt.grid(True)
plt.ylim(-120,40)
items = []
print('Starting loop ...')
while not quit:
    plot(fig,ax)
print('Quit')

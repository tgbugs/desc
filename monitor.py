import platform
import os

def win():
    pass

xrandr_indexes = (
    2,  # resolution
    -3,  # width
    -1,  # height
)
def lin():
    with os.popen('xrandr') as p:
        lines = p.readlines()
    size_lines = [l for l in lines if l.count('mm') == 2]
    #means = []
    ppmm_hs = []
    #return the highest ppmm found
    for line in size_lines:
        fields = line.rstrip().split(' ')
        res, width, height = [fields[i] for i in xrandr_indexes]
        x, y = [int(r) for r in res.split('+')[0].split('x')]
        w, h = [int(v.rstrip('mm')) for v in (width, height)]
        
        ppmm_w = x/w
        ppmm_h = y/h
        mean = .5 * (h*x + w*y) / (w*h)
        print('ppmm width', ppmm_w)
        print('ppmm height', ppmm_h)
        print('ppmm mean', mean)
        #means.append(mean)
        ppmm_hs.append(ppmm_h)
    
    #return max(means)
    return max(ppmm_hs)


def osx():
    pass

def getMaxPixelsPerMM():
    """ returns the maximum pixels per mm for the height (vertical direction) across all displays """
    doit = {'Darwin': osx,
            'Linux': lin,
            'Windows': win,
           }
    return doit[platform.system()]()

def main():
    print(getMaxPixelsPerMM(), 'pixels per mm')

if __name__ == '__main__':
    main()

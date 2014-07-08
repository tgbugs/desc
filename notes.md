if we can get 3.4 to work then we can use from concurrent.futures import ThreadPoolExecutor
rather from concurrent.futures import ProcessPoolExecutor
better yet with the yield trick we can make it a multiprocessing pool?

check out those screencaps, we are rendering 99999 * 99 (100000 * 100 = 1E7) collision nodes at 30 fps +, freeking magic man, of course rendering those 10 million objects does take about 20 gigs of ram and an hour and a half to generate and call run() on 

hrm, it does infact look like things are actually getting culled and that is driving the speedup, awesome

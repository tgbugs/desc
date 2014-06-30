if we can get 3.4 to work then we can use from concurrent.futures import ThreadPoolExecutor
rather from concurrent.futures import ProcessPoolExecutor
better yet with the yield trick we can make it a multiprocessing pool?

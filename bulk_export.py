"""
docstring here

"""
import sys
import urllib
from time import sleep
import json
import pickle
import argparse

from skytap.Templates import Templates
from skytap.Exports import Exports

download_dir = '/Users/bwellington/Downloads'
queue_file = "queue.p"
download_file = "downloads.p"

jobs = Exports()

def pickle_add(l, pickle_file):
    c = pickle_load(pickle_file)
    p = list(set(l).union(c))
    pickle_dump(p, pickle_file)

def pickle_remove(i, pickle_file):
    c = pickle_load(pickle_file)
    while i in c: c.remove(i)
    pickle_dump(c, pickle_file)

def pickle_dump(l, pickle_file):
    try:
        pickle.dump( l, open( pickle_file, "wb" ) )
    except:
        print "could not write to pickle file"

def pickle_load(pickle_file):
    try:
        l = pickle.load(open( pickle_file, "rb" ) )
    except:
        l = []

    return l

def pickle_clear(pickle_file):
    l = []
    pickle_dump(l, pickle_file)

def pickle_list(pickle_file):
    l = pickle_load(pickle_file)
    print l

# get list of vm ids in the template
def list_vms(template_id):
    template = Templates()[template_id]
    for vm in template.vms:
        print vm.id

def queue_jobs(template_id):
    template = Templates()[template_id]
    queue = pickle_load(queue_file)
    for vm in template.vms:
        queue.append(vm.id)
    pickle_add(queue, queue_file)
    return queue


def create_jobs():
    queue = pickle_load(queue_file)
    for vm in queue:
        try:
            Exports().create(vm)
            sleep(5)
            while vm in queue:
                queue.remove(vm)
                pickle_remove(vm, queue_file)
        except Exception as e:
            err = e.message
            if (err['status_code'] == 422):
                print "All import/export slots full"
            print "Error creating export jobs"
            pass

def list_jobs():
    for job in jobs:
        print job.id, job.vm_name, job.status

def download_export():
    for job in jobs:
        if job.status == 'complete':
            try:
                active = pickle_load(download_file)
                if job.id not in active:
                    active.append(job.id)
                    pickle_add(active, download_file)
                    print "Downloading Job " + str(job.id)
                    urllib.urlretrieve(job.ftp_url, download_dir + '/' +
                    str(job.id) + '_' +job.vm_name + '.7z')
                    delete_job(job.id)
                    sleep(5)
                    active = pickle_load(download_file)
                    while job.id in active:
                        active.remove(job.id)
                        pickle_remove(job.id, download_file)
                else:
                    pass

            except:
                print "Unable to download job " + str(job.id)
                pass

        elif job.status == 'processing':
            print 'Job ' + str(job.id) + ' is still processing.'

        elif job.status == 'error':
            print 'Error creating export job ' + str(job.id)

        else:
            print 'An unspecified error has occured.'

def delete_job(id):
    Exports().delete(id)

def delete_jobs():
    for job in jobs:
        Exports().delete(job.id)




if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-q", "--queue", help="Queue up all the VMs in the template for exporting.  Takes a template_id as an argument.")
    group.add_argument("-e", "--export", action="store_true", default=False, help="Create export jobs from the VMs currently in the queue.")
    group.add_argument("-d", "--download", action="store_true", default=False, help="Download \"completed\" export job from Skytap.")
    group.add_argument("--list_exports", action="store_true", default=False, help="Display current exports.")
    group.add_argument("--list_active_downloads", action="store_true", default=False, help="Display active downloads.")
    group.add_argument("--list_queue", action="store_true", default=False, help="Display current queue.")
    group.add_argument("--clear_queue", action="store_true", default=False, help="Clear all remaining items in the queue.")
    group.add_argument("--clear_active_downloads", action="store_true", default=False, help="Clear all remaining active downloads.")
    group.add_argument("--delete_all", action="store_true", default=False, help="This will delete all completed exports and clear the queue.")

    result =  parser.parse_args()

    if result.queue:
        queue_jobs(int(result.queue))

    if result.export:
        create_jobs()

    if result.download:
        download_export()

    if result.list_exports:
        list_jobs()

    if result.list_queue:
        pickle_list(queue_file)

    if result.list_active_downloads:
        pickle_list(download_file)

    if result.clear_queue:
        pickle_clear(queue_file)

    if result.clear_active_downloads:
        pickle_clear(download_file)

    if result.delete_all:
        delete_jobs()
        pickle_clear(queue_file)
        pickle_clear(download_file)

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

jobs = Exports()

def queue_dump(queue):
    try:
        pickle.dump( queue, open( queue_file, "wb" ) )
    except:
        print "could not write to pickle file"

def queue_load():
    try:
        queue = pickle.load( open( queue_file, "rb" ) )
    except:
        queue = []

    return queue

def clear_queue():
    queue = []
    queue_dump(queue)


# def dequeue(vm):
#     while vm in queue: queue.remove(vm)

# get list of vm ids in the template
def list_vms(template_id):
    template = Templates()[template_id]
    for vm in template.vms:
        print vm.id

def queue_jobs(template_id):
    template = Templates()[template_id]
    queue = queue_load()
    for vm in template.vms:
        queue.append(vm.id)
    queue_dump(queue)
    return queue


def create_jobs():
    queue = queue_load()
    for vm in queue:
        try:
            Exports().create(vm)
            sleep(5)
            while vm in queue: queue.remove(vm)
        except Exception as e:
            err = e.message
            print err
            if (err['status_code'] == 422):
                print "All slots full"
            print ("error creating export jobs")
            pass

        finally:
            queue_dump(queue)

# def list_jobs():
#     for job in jobs:
#         print job.id, job.vm_name, job.status

def download_export():
    for job in jobs:
        if job.status == 'complete':
            try:
                urllib.urlretrieve(job.ftp_url, download_dir + '/' +
                str(job.id) + '_' +job.vm_name + '.7z')
                delete_job(job.id)

            except Error:
                print("Something went wrong with the download")

        elif joh.status == 'processing':
            print 'Job ' + job.id + 'is still processing.'

        elif job.status == 'error':
            print 'Error creating export job' + job.id

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
    group.add_argument("--clear_queue", action="store_true", default=False, help="Clear all remaining items in the queue.")
    group.add_argument("--delete_all", action="store_true", default=False, help="This will delete all completed exports and clear the queue.")

    result =  parser.parse_args()

    if result.queue:
        queue_jobs(int(result.queue))

    if result.export:
        create_jobs()

    if result.download:
        download_export()

    if result.clear_queue:
        clear_queue()

    if result.delete_all:
        delete_jobs()
        clear_queue()

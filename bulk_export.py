


import sys
import urllib
from time import sleep
import json
import argparse
import threading
import Queue
import logging

from skytap.Templates import Templates
from skytap.Exports import Exports

download_dir = '/Users/bwellington/Downloads'

logger = logging.getLogger('bulk-vm-export')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

vm_queue = Queue.Queue(maxsize = 0)
dl_queue = Queue.Queue(maxsize = 0)


def build_vm_queue(template_id):
    '''Load all the VMs from the template into the vm_queue'''
    template = Templates()[template_id]
    for vm in template.vms:
        vm_queue.put(vm.id)

def create_jobs(vm_queue):
    '''pop a VM id from the vm_queue and create a Skytap export job.'''
    while True:
#        logger.debug(threading.current_thread().name,"exporter")
        vm = vm_queue.get()
        logger.info("Create export job for VM " + str(vm) +".")
        try:
            vm = export_queue.get(False)
            j = Exports().create(vm)
            sleep(5)
            job = Exports()[j]
            logger.info("Add export Job " + str(job.id) + " to dl_queue.")
            dl_queue.put(job) # add new export object to the dl_queue
            vm_queue.task_done()

        except Queue.Empty:
            logger.error("The vm_queue is empty.")
            continue

        except Exception as e:
            err = e.message
            # print err
            try:
                if (err['status_code'] == 422):
                    print("All import/export slots full.  Returning " + str(vm) + " to queue.")
                    export_queue.put(vm)
                    export_queue.task_done()
                    sleep(60)

            except:
                    print("Error creating export jobs.")
                    print err
                    export_queue.task_done()

            vm_queue.put(vm)
            sleep(60)
            continue

def build_download_queue():
    '''add the existing list of exports to the dl_queue'''
    logger.info("Check for existing exports and add them to the dl_queue.")
    jobs = Exports()
    for job in jobs:
        dl_queue.put(job)


def download_jobs(dl_queue):
    '''download export jobs form skytap and cleanup when finished'''
    while True:
#        logger.debug(threading.current_thread().name,"downloader")
        j = dl_queue.get()
        try:
            if j.status == "processing":
                logger.info("Job " + str(j.id) + " Status: " + str(j.status))
                refresh_job = Exports()[j.id]
                dl_queue.put(refresh_job)
                dl_queue.task_done

            elif j.status == 'complete':
                logger.info("Job " + str(j.id) + " Status: " + str(j.status))
                logger.info("Downloading Job " + str(j.id))
                urllib.urlretrieve(j.ftp_url, download_dir + '/' +
                str(j.id) + '_' +j.vm_name + '.7z')
                delete_job(j.id)
                dl_queue.task_done()
            else:
                dl_queue.put(j)
                logger.info("Job " + str(j.id) + " Status: " + str(j.status))

        except Queue.Empty:
            logger.error("The dl_queue is empty.")
            continue

        sleep(60)

def delete_job(id):
    Exports().delete(id)


##########################
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--template", help="Queue up all the VMs in the template for exporting." +
    "  Takes a template_id as an argument.")
    parser.add_argument("-d", "--downloaders", help="Number of download threads to use." +
    " This number is limited only by available memory.  However, Skytap accounts have a specific " +
    " number of import/export depots.  It will serve no purpose to have more download threads" +
    " than you have export depots. Default: 3 ")
    result = parser.parse_args()

    if result.downloaders > 0:
        dl_threads = int(result.downloaders)
    else:
        dl_threads = 3

    for i in range(dl_threads):
        '''Set up the download threads.'''
        downloader = threading.Thread(target=download_jobs, args=(dl_queue,))
        downloader.setDaemon(False)
        downloader.start()

    template_id = int(result.template)
    if result.template:
        '''Set up the vm queue thread.'''
        build_vm_queue(template_id)

        exporter = threading.Thread(target=create_jobs, args=(vm_queue,))
        exporter.setDaemon(False)
        exporter.start()

    build_download_queue()

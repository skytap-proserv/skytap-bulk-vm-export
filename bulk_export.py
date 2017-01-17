


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

# setup logger
logger = logging.getLogger('bulk-vm-export')
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

#setup queues
export_queue = Queue.Queue(maxsize = 0)
failed_downloads = Queue.Queue(maxsize = 0)


def build_export_queue(templates):
    '''Load all the VMs from the template into the export_queue'''
    for id in templates:
        template = Templates()[id]
        for vm in template.vms:
            export_queue.put(vm.id)

def create_jobs(export_queue):
    '''pop a VM id from the export_queue and create a Skytap export job.'''

    while True:
#        logger.debug(threading.current_thread().name,"exporter")

        try:
            vm = export_queue.get(False)
            logger.info("Create export job for VM " + str(vm) +".")
            j = Exports().create(vm)
            sleep(5)

            #create a downloader thread for this job
            downloader = threading.Thread(target=download_job, args=(j,))
            downloader.setDaemon(False)
            downloader.start()

            export_queue.task_done()

        except Queue.Empty:
            logger.error("The export_queue is empty.")
            return

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

            continue

def download_job(j):
#    '''download export jobs from skytap and cleanup when finished'''
    logger.debug("Start Download Thread: " + threading.current_thread().name,str(j) + " downloader")
    while True:
        try:
            job = Exports()[j]
        except:
            logger.error("Unable to locate job " + str(j) +".  Are you sure it exists?")
            failed_downloads.put(job.id)
            return

        if job.status == "processing":
            logger.info("Job " + str(job.id) + " Status: " + str(job.status) )
            logger.info("Job " + str(job.id) + " Refreshing.")
            job = Exports()[job.id]
            sleep(60)
            continue

        elif job.status == 'complete':
            try:
                logger.info("Job " + str(job.id) + " Status: " + str(job.status))
                logger.info("Downloading Job " + str(job.id))
                urllib.urlretrieve(job.ftp_url, download_dir + '/' +
                str(job.id) + '_' +job.vm_name + '.7z')
                delete_job(job.id)
                logger.info("Job " + str(job.id) + " downloaded successfully!")
                return

            except:
                logger.error("Download failed.  Try downloading this job again using bulk-export -o " + download_dir + "-d " + str(job.id) + ".")
                failed_downloads.put(job.id)
                return

        else:
            logger.error("Something went wrong")
            return

def delete_job(id):
    Exports().delete(id)

def list_failed_downloads(failed_downloads):
    l = []
    while True:
        try:
            f = failed_downloads.get(False)
            l.append(f)
            failed_downloads.task_done()
            return l

        except:
            return l



##########################
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_dir", type=str, help="path to output directory.")
    parser.add_argument("-t", "--templates", nargs='+', type=int, help="export a list of templates.  Takes space delimited template IDs as arguments.")
    parser.add_argument("-v", "--vms", nargs='+', type=int, help="export a list of virtual machines.  Takes space delimited VM IDs as arguments.")
    parser.add_argument("-d", "--download", type=int, help="download a single job.  Takes single export job ID as an argument.")
    result = parser.parse_args()

    if result.output_dir:
        download_dir = result.output_dir


    templates = result.templates
    if result.templates:
        '''Set up the vm queue thread.'''
        build_export_queue(templates)
        create_jobs(export_queue)

    vms = result.vms
    if result.vms:
        '''Set up the vm queue thread.'''
        for vm in vms:
            export_queue.put(vm)
        create_jobs(export_queue)

    download = result.download
    if result.download:
        '''Download single job.'''
        download_job(download)




    # check for failed Downloads
    l = list_failed_downloads
    if l:
        print "The following downloads failed to complete:"
        print '\n'.join(map(str, l))
        print "You may attempt to download them again using the follwoing commands:"
        for i in l:
            print "bulk-export.py -o " + download_dir + "-d " + str(i)

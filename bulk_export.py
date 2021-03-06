#!/usr/bin/env python
#
# bulk_export.py
# v.2017-01-20
#
# by Bill Wellington (bwellington@skytap.com)


# import some modules
import os
import sys
import re
import urllib
from time import sleep
import json
import argparse
import threading
import Queue
import logging

try:
    import pathvalidate
except:
    print('the module "pathvalidate" is required.  Please install using "pip install pathvalidate".')


try:
    from skytap.Templates import Templates
    from skytap.Exports import Exports
except:
    print('the module "skytap" is required.  Please install using "pip install skytap".')

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
        try:
            template = Templates()[id]
            for vm in template.vms:
                export_queue.put(vm.id)

        except KeyError:
            logger.error("The template " + str(id) + " no longer exists. Continuing.")
            continue

def create_jobs(export_queue):
    '''pop a VM id from the export_queue and create a Skytap export job.'''

    while True:
#        logger.debug(threading.current_thread().name,"exporter")

        try:
            vm = export_queue.get(False)
            logger.info("Create export job for VM " + str(vm) +".")
            j = Exports().create(vm)
            sleep(5)

            #create a downloader thread for this export job
            downloader = threading.Thread(target=download_job, args=(j,))
            downloader.setDaemon(False)
            downloader.start()

            export_queue.task_done()

        except Queue.Empty:
            logger.error("The export_queue is empty.  Exiting.")
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
    '''download export jobs from skytap and cleanup when finished.'''
    logger.debug("Start Download Thread: " + threading.current_thread().name,str(j) + " downloader")
    while True:
        try:
            job = Exports()[j]
        except KeyError:
            logger.error("Download job " + str(j) + " no longer exists.")
            return

        if job.status == "processing":
            logger.info("Job " + str(job.id) + " Status: " + str(job.status) )
            logger.info("Job " + str(job.id) + " Refreshing.")
            job = Exports()[job.id]
            sleep(60)
            continue

        elif job.status == 'complete':
            download_dir = create_download_directory(str(job.template_url))
            try:
                logger.info("Job " + str(job.id) + " Status: " + str(job.status))
                logger.info("Downloading Job " + str(job.id))
                posix_vm_name = sanitize_posix(str(job.vm_name))
                urllib.urlretrieve(job.ftp_url, download_dir + '/' +
                str(job.id) + '_' + posix_vm_name + '.7z')
                delete_job(job.id)
                logger.info("Job " + str(job.id) + " downloaded successfully!")
                return

            except:
                logger.error("Download failed.  Try downloading this job again using bulk_export.py -o " + outbut_dir + "-d " + str(job.id) + ".")
                failed_downloads.put(job.id)
                return

        else:
            logger.error("There was a problem. Job ID: " + str(job.id) + " Status: " + str(job.status) + ".")
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

def create_download_directory(template_url):
    template_id = template_url.rsplit('/', 1)[-1]
    template_name = Templates()[int(template_id)]
    posix_template_name = sanitize_posix(str(template_name))
    download_dir = output_dir + '/' + str(template_id)  + "_" + str(posix_template_name)
    try:
        if not os.path.exists(str(download_dir)):
            os.makedirs(str(download_dir))
    except:
        logger.error("download directory " + download_dir + " cannot be created.")
    return download_dir

def sanitize_posix(string):
    f = pathvalidate.sanitize_filename(str(string))
    posix = "\\'".join("'" + p + "'" for p in f.split("'"))
    return posix

##########################
if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output_dir", type=str, help="Path to output directory.  A directory with the template ID will be created here, and your VMs will be placed inside.")
    parser.add_argument("-t", "--templates", nargs='+', type=int, help="Export a list of templates.  Takes space delimited template IDs as arguments.")
#    parser.add_argument("-v", "--vms", nargs='+', type=int, help="Export a list of virtual machines.  Takes space delimited VM IDs as arguments.")
    parser.add_argument("-d", "--download", type=int, help="Download a single job.  Takes single export job ID as an argument.")
    result = parser.parse_args()

    if result.output_dir:
        output_dir = result.output_dir


    templates = result.templates
    if result.templates:
        '''Set up the vm queue thread.'''
        build_export_queue(templates)
        create_jobs(export_queue)

    # this will be for a future feature - to add the ability to download specific VMs
    # vms = result.vms
    # if result.vms:
    #     '''Set up the vm queue thread.'''
    #     for vm in vms:
    #         export_queue.put(vm)
    #     create_jobs(export_queue)

    download = result.download
    if result.download:
        '''Download single job.'''
        download_job(download)




    # list of failed Downloads // not working right now - coming soon
    # l = list_failed_downloads
    # if l:
    #     print "The following downloads failed to complete:"
    #     print '\n'.join(map(str, l))
    #     print "You may attempt to download them again using the follwoing commands:"
    #     for i in l:
    #         print "bulk-export.py -o " + download_dir + "-d " + str(i)

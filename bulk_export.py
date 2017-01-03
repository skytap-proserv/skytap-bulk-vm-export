"""
docstring here

"""
import sys

from skytap.Templates import Templates
from skytap.Exports import Exports

jobs= Exports()

# get list of vm ids in the template
def list_vms(template_id):
    template = Templates()[template_id]
    for vm in template.vms:
        print vm.id

def create_jobs(template_id):
    template = Templates()[template_id]
    for vm in template.vms:
        Exports().create(vm.id)

def list_jobs():
    for job in jobs:
        print job.id, job.vm_name, job.status

def delete_jobs():
    for job in jobs:
        Exports().delete(job.id)


if __name__ == '__main__':

    delete_jobs()

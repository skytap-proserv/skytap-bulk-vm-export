"""
docstring here

"""

from skytap.Templates import Templates
from skytap.Exports import Exports

template = Templates()[936865]
jobs= Exports()

# get list of vm ids in the template
def list_vms():
    for vm in template.vms:
        print vm.id

def list_jobs():
    for job in jobs:
        print job.id, job.vm_name

def delete_jobs():
    for job in jobs:
        Exports().delete(job.id)



if __name__ == '__main__':

    Exports.delete_export_job()[122840]

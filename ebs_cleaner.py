import boto3

'''
Author: Jose Pico
Description: This lambda function scans all EBS volumes in unattached state (available) to perform
             a cleanup task by creating a snapshot and delete the volume.

'''

# Set the global variables according to your account
globalVars  = {}
globalVars['REGION_NAME']           = "ap-southeast-2"
globalVars['findNeedle']            = "Name"
globalVars['tagsToExclude']         = "Do-Not-Delete"
globalVars['RetentionTag']          = "UnattachedEBS"
ec2 = boto3.resource('ec2', region_name = globalVars['REGION_NAME'] )

def lambda_handler(event, context):

    deletedVolumes = { 'DeletedEBSVolumes':[], 'Snapshots':[],}
    # Get all the volumes in the region
    volumes = ec2.volumes.all()
    for vol in volumes:
        if  vol.state=='available':
            # Check for Tags
            if vol.tags is None:
                vid=vol.id
                v=ec2.Volume(vid)

                # Create snapshot for the volume before deletion
                snap = ec2.create_snapshot(VolumeId=vol.id, Description='Snapshot created by Lambda cleanup function ({})'.format(vid))
                snap.create_tags(Tags=[{'Key':globalVars['findNeedle'], 'Value':globalVars['RetentionTag']}])

                # Delete unattached volume with no tags
                v.delete()
                deletedVolumes['DeletedEBSVolumes'].append({'VolumeId': vid,'Status':'Delete Initiated'})
                deletedVolumes['Snapshots'].append({'SnapshotId': snap.id,'Status':'Snapshot created'})
            else:
                for tag in vol.tags:
                    tag['Key'] == globalVars['findNeedle']
                    value=tag['Value']
                    if value != globalVars['tagsToExclude'] and vol.state == 'available' :
                        vid = vol.id
                        v = ec2.Volume(vid)
                        # Create snapshot for the volume before deletion
                        snap = ec2.create_snapshot(VolumeId=vol.id, TagSpecifications = [
                            {
                                'ResourceType': 'snapshot',
                                'Tags': vol.tags,

                            },
                        ], Description='Snapshot created by Lambda cleanup function ({})'.format(vid))

                        # Delete unattached volume with no tags
                        v.delete()
                        deletedVolumes['DeletedEBSVolumes'].append({'VolumeId': vid,'Status':'Delete Initiated 2'})
                        deletedVolumes['Snapshots'].append({'SnapshotId': snap.id,'Status':'Snapshot created'})

    # If no Volumes are deleted, return consistent json output for volumes and snapshots
    if not deletedVolumes['DeletedEBSVolumes']:
        deletedVolumes['DeletedEBSVolumes'].append({'VolumeId':None,'Status':None})
        deletedVolumes['Snapshots'].append({'SnapshotId':None,'Status':None})


    # Return the list of status of the snapshots triggered by lambda as list
    print (deletedVolumes)
    return deletedVolumes
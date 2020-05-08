#!/usr/bin/env python
# this Python file uses the following encoding: utf-8

## This script is the emergency manager node developed to decide what is the best action 
# to take in the U-space when some Threats are showed up.

import os, sys
import rospy
import time
from math import sqrt
from gauss_msgs.srv import Threats, ThreatsResponse, ThreatsRequest
from gauss_msgs.srv import ReadOperation, ReadOperationRequest, ReadOperationResponse
from gauss_msgs.srv import WriteGeofences, WriteGeofencesRequest, WriteGeofencesResponse
from gauss_msgs.msg import Threat, Notification, Waypoint, WaypointList, Operation, Geofence
#from gauss_msgs.srv import Deconfliction, DeconflictionRequest

class EmergencyManagement():

    def __init__(self): 
        
        # Initialization
        self._threats2solve = ThreatsRequest()        

        # Publish

        self._notification_publisher = rospy.Publisher('notification', Notification, queue_size=1)
        
        # Wait until service is available and creat connection
        
        #rospy.wait_for_service('/gauss/deconfliction')                    
        #self._requestDeconfliction_service_handle = rospy.ServiceProxy('/gauss/deconfliction', Deconfliction) 

        rospy.wait_for_service('/gauss/read_operation')                    
        self._readOperation_service_handle = rospy.ServiceProxy('/gauss/read_operation', ReadOperation) 

        rospy.wait_for_service('/gauss/write_geofences')                    
        self._writeGeofences_service_handle = rospy.ServiceProxy('/gauss/write_geofences', WriteGeofences) 
               
    # Server     

        self._threats_service = rospy.Service('gauss/threats', Threats, self.service_threats_cb) 
        print("Ready to add a threat request")
    
    #TODO link Threats severity/probability with the SoA references.
    
    #def assign_threat_severity(self):
        #self._threats_definition = {
        #                            Threat.UAS_IN_CV: {'type': 'conflict', 'severity': 1},
        #              	            Threat.UAS_OUT_OV: {'type': 'conflict', 'severity': 2},
        #                            Threat.LOSS_OF_SEPARATION: {'type': 'conflict', 'severity': 2},
        #                            Threat.ALERT_WARNING: {'type': 'alert', 'severity': 2},
        #                            Threat.GEOFENCE_INTRUSION: {'type': 'conflict', 'severity': 2},
        #                            Threat.GEOFENCE_CONFLICT: {'type': 'conflict', 'severity': 1},
        #                            Threat.TECHNICAL_FAILURE: {'type': 'alert', 'severity': 3},
        #                            Threat.COMMUNICATION_FAILURE: {'type': 'alert', 'severity': 3},
        #                            Threat.LACK_OF_BATTERY: {'type': 'conflict', 'severity': 1},
        #                            Threat.JAMMING_ATTACK: {'type': 'alert', 'severity': 2},
        #                            Threat.SPOOFING_ATTACK: {'type': 'alert', 'severity': 3}
        #                            }
   
       
    def action_decision_maker(self,threats2solve):
        events = threats2solve.threats
        threat_id = events[0].threat_id
        #threat_type = self._threats_definition[threat_id]['type']
        #threat_severity = self._threats_definition[threat_id]['severity']
        #first_operation_priority = self._operation_info_from_db['operations'][0]['priority']
        #second_operation_priority = self._operation_info_from_db['operations'][1]['priority']
        
        #We send a message for going back to the FG to the UAV in conflict.
        if threat_id == Threat.UAS_IN_CV: #UAS IN CV
            uav_ids = events[0].uav_ids
            uav_id = uav_ids[0]
            #Publish the action which the UAV has to make.
            notification = Notification()
            notification.description = 'Go back to your flight plan.'
            notification.uav_id = uav_id
            self._notification_publisher.publish(notification) 
        
        #We 
        if threat_id == Threat.UAS_OUT_OV: #UAS_OUT_OV
            action = 'URGENT: Land as soon as possible.'  
        
        #We 
        if threat_id == Threat.LOSS_OF_SEPARATION: #LOSS_OF_SEPARATION
            action = 'Send new trajectories recommendations to the UAS involved in the conflict.'     

        #We
        if threat_id == Threat.ALERT_WARNING: #ALERT_WARNING
            action = 'Ask for a Geofence creation and send an alert report to all the pilots.' 

        #We
        if threat_id == Threat.GEOFENCE_INTRUSION: #GEOFENCE_INTRUSION
            action = 'Ask for leaving the geofence asap and continue its operation.' 

        #We
        if threat_id == Threat.GEOFENCE_CONFLICT: #GEOFENCE_CONFLICT
            action = 'Send new trajectory recommendation to the UAS involved in the conflict.'     
        
        #We send a message for landing now to the UAV in conflict.
        if threat_id == Threat.TECHNICAL_FAILURE: #TECHNICAL_FAILURE
            uav_ids = events[0].uav_ids # Esto sería la lista de uavs implicados.
            #TODO coger todos los el uav_id de la operación implicados para resolver y mandar una notificación?
            uav_id = uav_ids[0]
            request = ReadOperationRequest()
            request.uav_ids = uav_id
            response = ReadOperationResponse()
            response = self.send_uav_ids(request) 
            #Publish the action which the UAV has to make.
            notification = Notification()
            notification.description = 'URGENT: Land now.'
            notification.uav_id = uav_id
            self._notification_publisher.publish(notification)           
            # We create a geofence.
            geofence = Geofence()
            geofence.id = 3
            geofence.min_altitude = 0.0
            geofence.max_altitude = 100.0
            # We write a geofence.
            request = WriteGeofencesRequest()
            request.geofence_ids = [geofence.id]
            request.geofences = [geofence]
            response = WriteGeofencesResponse()
            response = self._writeGeofences_service_handle(request)
            response.message = "Geofence stored in the Data Base"
            print(response.message)
            action = 'Send new trajectory recommendation to the UAS involved in the conflict.'     
        
        #We
        if threat_id == Threat.COMMUNICATION_FAILURE: #COMMUNICATION_FAILURE
            action = 'URGENT: Land as soon as possible.' 

        #We    
        if threat_id == Threat.LACK_OF_BATTERY: #LACK_OF_BATTERY
            action = 'URGENT: Land as soon as possible.' 
        
        #We
        if threat_id == Threat.JAMMING_ATTACK: #JAMMING_ATTACK
            action = 'URGENT: Land as soon as possible.'  
        
        #We
        if threat_id == Threat.SPOOFING_ATTACK: #SPOOFING_ATTACK
            action = 'URGENT: Land as soon as possible.'  

    def service_threats_cb(self, request):
        rospy.loginfo("New threat received:") 
        response = ThreatsResponse()
        response.success = True
        self._threats2solve = request # ThreatsRequest
        self._threats2solve.uav_ids = list(request.uav_ids) 
        self.action_decision_maker(self._threats2solve)      
        return response        

   ## Since a Threat has been received. It is request operation info of the UAV linked to
   # the Threat. 

    def send_uav_ids(self, request): 
        return self._readOperation_service_handle(self._threats2solve.uav_ids)
  
    
    #def declare_new_trajectory_parameters (self):
    #    pass

    #def request_new_trajectory(self):
    #    request = DeconflictionRequest()
    #    #TODO, rellenar la info necesaria para que me envien una nueva trayectoria.
    #    pass
    
    #def write_new_flight_plan(self):
    #    request = WriteFlightPlanRequest()
    #    #TODO, rellenar la info necesaria para poder escribir un nuevo flight plan.
    #    pass

    #def activate_fts(self, fts_signal): # Flight Termination System
    #    self._notification_publisher.publish(fts_signal)

    #TODO, definir los parametros para usar esta función.
    
    #def calculate_best_landingspot(self):
    #    pass

''' The node and the EmergencyManagement class are initialized'''

if __name__=='__main__':

    rospy.init_node('emergency_management')
    e = EmergencyManagement()
    #e.assign_threat_severity()
    rospy.spin()   


    

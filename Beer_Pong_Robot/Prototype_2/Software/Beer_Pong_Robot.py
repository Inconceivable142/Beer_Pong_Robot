# import the necessary packages
import cv2
import numpy as np
import argparse
import glob
import imutils
import time
import math
import serial
#set up arduino serial connection
arduino = serial.Serial(port='/dev/ttyUSB0', baudrate=9600, timeout=1)
#flush arduino serial connection
arduino.flush()

time.sleep(10.0)

#camera resolution
resolution = [1920, 1080]
#delcare variable for tracking cup number and initialize to zero
cup = 0
#delcare variable for tracking the pixel location for the center of the last match
last_match_center = 0
#declare variable for the diameter of a cups rim and initialize to 3.75
rim_diameter = 3.75
#define the number of steps per degree
step_degree = 500/180

#define arduino read/write function
def write_read(x):
    arduino.write(str(x).encode('utf-8'))
    time.sleep(0.05)
    data = arduino.readline().decode('utf-8').rstrip()
    return data

def get_image():
    for x in range(6):
        ret, rgb_img = cap.read()
    
    return rgb_img

def mask_image(img):
    hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # lower boundary RED color range values; Hue (0 - 10)
    lower1 = np.array([0, 100, 20])
    upper1 = np.array([10, 255, 255])
     
    # upper boundary RED color range values; Hue (160 - 180)
    lower2 = np.array([160,100,20])
    upper2 = np.array([179,255,255])
     
    #use hsv boundaries to create upper and lower mask
    lower_mask = cv2.inRange(hsv_img, lower1, upper1)
    upper_mask = cv2.inRange(hsv_img, lower2, upper2)
     
    #combine for full mask
    full_mask = lower_mask + upper_mask;
     
    mskd_img = cv2.bitwise_and(img, img, mask=full_mask)

    gray_mskd_img = cv2.cvtColor(mskd_img, cv2.COLOR_RGB2GRAY)
    #cv2.imshow("masked image", gray_mskd_img)
               
    return gray_mskd_img

def crop_image(img, center):
    #crop image arround group
    cH, cW = 200, 300
    #crop the image to matched center +- 
    crpd_img = img[center[1] - int(0.5 * cH):center[1] + int(0.5 * cH), center[0] - int(0.5 * cW):center[0] + int(0.5 * cW)]
    
    return crpd_img

def find_template():
    #grab tempalte image
    template = cv2.imread('/home/pi/Desktop/Cup.jpg')
    #get height and width of template image
    (tH, tW) = template.shape[:2]

    gray_mskd_template = mask_image(template)
    #cv2.imshow("masked template", gray_mskd_template)
    
    return gray_mskd_template, tH, tW
    

def group_pos_crop(gray_mskd_template, tH, tW):
    
    #capture image
    rgb_img = get_image()
    rgb_img_copy = rgb_img.copy()
    
    gray_mskd_img = mask_image(rgb_img)
    #cv2.imshow("masked double upper/lower", gray_mskd_img)
    
    res = cv2.matchTemplate(gray_mskd_img, gray_mskd_template, cv2.TM_CCOEFF_NORMED)
    #get the min and max values of template
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #get the top left coordinates
    #Change to max_loc for all except for TM_SQDIFF
    top_left = max_loc
    #print(max_val) 
    #find the bottom right coordinates
    bottom_right = (top_left[0] + tW, top_left[1] + tH)
    #draw rectangle around image
    cv2.rectangle(rgb_img, top_left, bottom_right, (255, 0, 0), 2) 
    #show matched image
    #cv2.imshow("Matched image", rgb_img)
    center = (top_left[0] + int(0.5 * tW), top_left[1] + int(0.5 * tH))
    #crop the image to matched center +- 
    gray_mskd_crpd_img = crop_image(gray_mskd_img, center)
    crpd_img = crop_image(rgb_img_copy, center)
    #match template to image
    #need to look at what the best matching method is
    #res = cv2.ximgproc.colorMatchTemplate(crpd_img, template)
    res = cv2.matchTemplate(gray_mskd_crpd_img, gray_mskd_template, cv2.TM_CCOEFF_NORMED)
    #get the min and max values of template
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #get the top left coordinates
    #Change to max_loc for all except for TM_SQDIFF
    top_left = max_loc
    #find the bottom right coordinates
    #bottom_right = (top_left[0] + tW, top_left[1] + tH)
    crpd_center = (top_left[0] + int(0.5 * tW), top_left[1] + int(0.5 * tH))
    #draw rectangle around image
    #cv2.rectangle(crpd_img, top_left, bottom_right, (255, 0, 0), 2) 
    #show cropped matched image
    #cv2.imshow("Cropped Matched image", crpd_img)
    #set return value
    #centerTLX, centerTLY = top_left[0], top_left[1]
    #calculate center delta base on resolution
    CenDelt = (center[0] - (resolution[0]/2), center[1] - (resolution[1]/2))
    print("Delta from the center: ", CenDelt)
    return crpd_img, center, crpd_center, CenDelt
    #return centerTLX, centerTLY

def get_distance(crpd_img):
    
    crpd_img_copy = crpd_img.copy()
    
    blrd_img = cv2.blur(crpd_img,(5,5))
    #cv2.imshow("Blurred Image", blrd_img)

    gray_mskd_crpd_img = mask_image(blrd_img)
    ret, thres_img = cv2.threshold(gray_mskd_crpd_img, 5, 255, 0)
    #cv2.imshow("Image Wth Threshold Applied", thres_img)

    #not sure if eroding and dilating the image is best before or after thresholding
    eroded = cv2.erode(thres_img, None, 4)
    dilated = cv2.dilate(eroded, None, 4)

    #cv2.imshow('mask', full_mask)
    #cv2.imshow('dilated ', dilated)

    edgd_img = cv2.Canny(dilated, 35, 125)
    #cv2.imshow("Edged Image", edgd_img)

    cnts = cv2.findContours(edgd_img.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    c = max(cnts, key = cv2.contourArea)
    # compute the bounding box for the last row of cups
    marker = cv2.minAreaRect(c)
    
    #draw and show the bounding box for debug
    box = cv2.boxPoints(marker)
    box = np.int0(box)
    cv2.drawContours(crpd_img_copy, [box], 0, (0,0,255), 2)
    #cv2.imshow("Boxed Image", crpd_img_copy)

    #print(marker[1][1])
    # initialize the known distance from the camera to the object, which
    # in this case is 81.5 inches
    KNOWN_DISTANCE = 92
    # initialize the known object width, which in this case, the back row
    # of cups is 15.25 inches wide
    KNOWN_WIDTH = 15.25

    # load the first image that contains an object that is KNOWN TO BE 2 feet
    # from our camera, then find the paper marker in the image, and initialize
    # the focal length
    focalLength = 1405.81
    #focalLength = (marker[1][1] * KNOWN_DISTANCE) / KNOWN_WIDTH
    #print(focalLength)
    
    #off setting because camera is in front
    brDistance = ((KNOWN_WIDTH * focalLength) / marker[1][1])
    print("Distance to back row: ", brDistance)
    
    inches_per_pixel_w = KNOWN_WIDTH/marker[1][1]
    #print(pix_inch_w)
    
    return brDistance, inches_per_pixel_w

def firing_sequence(gray_mskd_template, center, crpd_center, brDistance, rim_diameter, inches_per_pixel_w, CenDelt):
    
    global cup
    global last_match_center
    
    response = write_read("goto," + str(0))
    print("Arduino response: ", response)
    
    time.sleep(10.0)
    
    #capture image
    rgb_img = get_image()
    rgb_img_copy = rgb_img.copy()
    
    gray_mskd_img = mask_image(rgb_img)
    gray_mskd_crpd_img = crop_image(gray_mskd_img, center)
    
    res = cv2.matchTemplate(gray_mskd_crpd_img, gray_mskd_template, cv2.TM_CCOEFF_NORMED)
    #get the min and max values of template
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    #get the top left coordinates
    #Change to max_loc for all except for TM_SQDIFF
    top_left = max_loc
    #print(max_val) 
    #find the bottom right coordinates
    bottom_right = (top_left[0] + tW, top_left[1] + tH)
    #draw rectangle around image
    cv2.rectangle(rgb_img, top_left, bottom_right, (255, 0, 0), 2) 
    #show matched image
    cv2.imshow("gray_mskd_crpd_img", gray_mskd_crpd_img)
    match_center = (top_left[0] + int(0.5 * tW), top_left[1] + int(0.5 * tH))
    #print(center[0])
    #print(match_center[0])
    
    if cup == 0:
    
        if ((crpd_center[0] - 10) > match_center[0]) or (match_center[0]> (crpd_center[0] + 10)):
            cup += 1
    else:
        
        if ((last_match_center[0] - 10) > match_center[0]) or (match_center[0] > (last_match_center[0] + 10)):
            cup += 1
            
    if cup == 0:
        adjacent = brDistance - (3 * rim_diameter)
        print("The length of the adjacent for the matched cup is: ", adjacent)
    elif cup == 1:
        adjacent = brDistance - (2 * rim_diameter)
        print("The length of the adjacent for the matched cup is: ", adjacent)
    elif cup == 2:
        adjacent = brDistance - (2 * rim_diameter)
        print("The length of the adjacent for the matched cup is: ", adjacent)
    elif cup == 3:
        adjacent = brDistance - rim_diameter
        print("The length of the adjacent for the matched cup is: ", adjacent)
    elif cup == 4:
        adjacent = brDistance - rim_diameter
        print("The length of the adjacent for the matched cup is: ", adjacent)
    elif cup == 5:
        adjacent = brDistance - rim_diameter
        print("The length of the adjacent for the matched cup is: ", adjacent)
    else:
        adjacent = brDistance
        print("The length of the adjacent for the matched cup is: ", adjacent)
        
    opposite = abs(match_center[0]-crpd_center[0]+CenDelt[0]) * inches_per_pixel_w
    print("The length of the opposite for the matched cup is: ", opposite)
    
    hypotenuse = math.sqrt(adjacent ** 2 + opposite ** 2)
    print("The length of the hypotenuse for the matched cup is: ", hypotenuse)
    
    #interpolate the fan speed from the hypotenuse
    fanSpeed = int(np.interp(hypotenuse, [71, 96], [105, 155]))
    print("The fan speed for the given hypotenuse is: ", fanSpeed)
    
    theta = math.degrees(math.atan(opposite/adjacent))
    print("The angle theta for the matched cup is: ", theta)
    
    step_direction = np.sign(match_center[0]-crpd_center[0]+CenDelt[0])
    steps = int(theta*step_degree*step_direction)
    print("The number of steps to move: ", steps)
       
    response = write_read("fire," + str(fanSpeed) + str(steps))
    print("Arduino response: ", response)   

    last_match_center = match_center
    
time.sleep(2.0)
#set capture object
cap = cv2.VideoCapture(0)
#set the resolution of the image to be captured
#full size 1920 x 1080
cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])

gray_mskd_template, tH, tW = find_template()

crpd_img, center, crpd_center, CenDelt = group_pos_crop(gray_mskd_template, tH, tW)

brDistance, inches_per_pixel_w = get_distance(crpd_img)

for x in range(10):
    firing_sequence(gray_mskd_template, center, crpd_center, brDistance, rim_diameter, inches_per_pixel_w, CenDelt)
    cv2.waitKey(0)

cv2.destroyAllWindows()

print(cup)

#ret, rgb_img = cap.read()

#cv2.imshow("Base Image", rgb_img)

# cv2.imwrite('/home/pi/Desktop/Cup.jpg',rgb_img)

#wait for response and destroy all windows
cv2.waitKey(0)
cv2.destroyAllWindows()

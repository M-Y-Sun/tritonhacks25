## Problem:
Unfortunately, we can’t always prevent crises from occurring. What we can do is strengthen our response when they do. In researching the true bottlenecks in disaster response—especially fires—we found a vivid account of the chaotic rescue efforts at Ground Zero on 9/11, where firefighters “didn’t know how many people were trapped alive…[as they] …had to search carefully through the unstable piles [of rubble]…” — HISTORY.com (on 9/11 Ground Zero). 343 firefighters died that day. This quote highlighted showed us, that if first responders had better access to vital information, like the exact number of people still inside a building, they could execute faster, safer rescues and save more lives.

## What & How:
In order to keep track of the number of people in a building, we planned on using security camera footage to track the number of people walking in and out (facing the exits). We then need to share these solutions with the First Responders so they can plan and act with confidence.

## Components
For recognizing the number of people in a building, we used Yolo open source v8 with Deepsort to track people in the camera's view, and used their positional data (and velocity data) to recognize when they entered or exited the building Since YOLO v8 doesn't have a class to recognize doors, we had to fine-tune YOLO-v8 using a Kaggle dataset of over 400 doors. We used hyperparameterization to fine-tune the model, and I trained it on my MacBook Air M3 across 30 epochs with a batch size of 32. We stored this information (constantly being updated) in a server hosted on our laptops (design flaw we will talk about later) We created a website that would let people, at the time of the crisis, send a quick message detailing the crisis (in addition to the location). We would then pair both of these informations, and format an automated response to send to 911 We used AI Twilio to create the audio recording, and show you all the final result

## Our Process
Constant iteration. We would go to the whiteboard and brainstorm ideas for each of our separate components, and devise ways to connect them all. We constantly pestered the friendly Mentors and Tutors and devised possible strategies/solutions. A lot of our work was inspired by the ideas of our mentors - just to name an example- we were introduced to the Yolo v8 model by Ultralytics, and it was super successful in recognizing and tracking humans.

And it wouldn’t always work. I remember having to test our Exit and Entry recognition countless times, I swear I can open every door on this campus with my eyes closed.

But most importantly, we all had an amazing time working together, creating and innovating with people we didn’t previously know!

Built With:
- css
- fastapi
- html
- javascript
- motion
- python
- react
- shadcn
- tailwind
- twilio
- typescript
- yolov8

# 15.06.2026
- In section Reflection, add learning outcomes and example evidences.
- Keeping the system on the edge eliminates privacy concerns.
- You can extend the system by addining acceleration or >1 object.
- Linear systems are easy for KF, but non-linear systems are challenging.

# 09.06.2026
- In the project report:
  - Add a section answering the research questions.
  - Mention that acceleration in KF may be beneficial.
- Handover section in the report:
  - Future developments, eg. DAv3. 
  - Explain how the project and its continuation fit in the broader context of HTES Lectoraat.
- Reflection section in the report (Professional Standard):
  - Explain the structured approach and process, what went well, what could be improved
  - Selected methodologies (reference Engineering design process/approach).
- After the final submission:
  - Understand better KF.
  - Check if the system can work with acceleration.

# 01.06.2026
- The detection error (5-6 cm) is not too bad.
- Check if there are other Docker containers running on Brum.
- Check if there is available base image for Jetson Jetpack.
- Check why it is not a good idea to add YOLO detection to the right image.
- Visualization of the actual and predicted trajectories can be separate graphs, not overlayed on the video.
- Maybe model predictive (control).
- A bouncing ball is not linear.
- Maybe try with acceleration (0, 0, 9,81) for gravity. Maybe KF will pick it up and learn acceleration.
- KF is optimal when noise is a normal distribution and there is no bias.

For the coming submission:
- Plan for integration (I/O) with Brum or other mobile robots - define API.
- Submit a baseline system.
- Camera detection accuracy vs manual detections -> analysis (histogram, maybe scatter plot).
- Add reading guide/project report with the main results and visualizations. Reference other evidences in it.

# 26.05.2026
Graduation Table Meeting 3
- The demo of the prototype was successful. Good experimental results. There was a huge step compared to the last graduation table when there was no demo.
- Think about handover documentation and git repo.
- You can try to record a video with a ball at the end of a pendulum to investigate gravity handling.
- The portfolio submission on June 5th is a rehearsal for the final submission. Most of the evidences should be there.
- Do not change the portfolio after the final submission. Some minor updates on the code and the demo for the presentation are fine.

# 20.05.2026
- Use standard measurement units (m, s) in the code and document them.
- Try out to run YOLO also on the right image, then take the weighted average of the two detections or the detection with higher confidence score. Make using YOLO twice will be beneficial.
- How heavy is it to run YOLO? Does it add too much compute power to add a YOLO function call for the second image?
- Document and justify the design choices: What components do you have? Why do you use them? What are the tradeoffs?
- Output the measurements and predictions in a CSV file.
- What is the internal state of the Kalman filter? Is it just position and velocity or there are other parameters?
- Investigate and document the operation of the Kalman filter (and the prototype in general) - how do the identity and measurement metrics work, what is a const velocity model; give names to variables.
- Try to add acceleration to the Kalman filter.
- Do analysis on the measurement accuracy and predictions.
- Make measurements by hand and compare them with the YOLO detection. Pick several points and manually analyze the frame when the ball is on that position. The goal is to have ground truth accuracy for the detection step. E.g., YOLO says that the ball x = 1 m, I measure that x = 1.03 by hand (independent measurement of detection). This means that the YOLO measurement is accurate with +/-5% buffer.
- Think about project handover.
- If in the next semester, you want to work on JEPA, the current system can be used as a benchmark.

# 11.05.2026
- Make videos with a grid/unit system.
- Discuss what "a modular system" means in this case with the product owner.
- Converting between RGB-D and point cloud shouldn't be a big problem. Algorithm design shouldn't depend too much on the input data representation.
- Detect objects (x, y, z), maybe also mass, velocity, acceleration, jurk -> Kalman filter -> prediction (+ uncertainty)
- What are the possible solutions? - research question
- Take a look at Engineering design approach.
- Make an MVP with Kalman filter.

# 20.04.2026
- Develop a simple case: track and predict 1 moving object (e.g., ball) with const velocity. Scope the MVP.
- Don't spend too much time on V-JEPA. Maybe the tech isn't ready for my use case.
- 1st simple case for video dataset: ball or person.
- 2nd more complex cases.

# 13.04.2026
- In the portfolio you want to tell a story and all evidences should support the story.
- Process document/Reading guide -> summary of the project: main problem, research questions, steps  taken. Describes the process and diff outcomes.
- What is the main problem to understand your assignment? Why didn't you focus on this -> this is my focus because XYZ
- Check online: ray casting, indexing mask for object detection, https://graduationconference-fontysict.nl/nl/, MCP - Model Context Protocol; framework for AI models; LSTM data; https://www.sac-nederland.nl/; GEA https://www.gea.com/en/
- Make a concrete experiment.
- Stop researching when you have a concrete goal.
- You narrowed down, but need to narrow down the project goal more.
- Your project can use a segmentation mask.
# 30.03.2026
- Check latency requirements with Martin and Edwin -> ensure it's fast enough so it doesn't collide with people
- Maybe Jetson Nano isn't powerful enough; use Jestson Orin
- Maybe apply trimming (cut off the background)
- Segmentation on a depth map?
- Look at this YOLO link: https://arxiv.org/pdf/2403.00175
- Good progress with narrowing down the scope and getting more concrete
- Final presentation:
	- Publicly accessible in a room at R10
	- Tell how many people will attend in advance
	- 20 min presentation (show a demo)
	- Q&A from the audience
	- Q&A from the assessors
	
# 20.03.2026
First portfolio submission from Mark (orienting on everything):
- LO1 Professional Duties: Good initial research document. This is fine for this early stage. For next time, I would like to see more of a motivated decision, preferably supported by hard data.
- LO2 Situation Orientation: I see some valuable ideas that might lead to demonstrable value for stakeholders, but it will be essential to start go from the initial wide brainstorm type of approach to a more focused effort.
- LO3 Professional Standards: Good start

# 16.03.2026
First company visit with Mark and Edwin - narrowing down the scope:
- In the coming weeks focus on ZED SDK and its API: body tracking, positional tracking,... Probably the features of detection and tracking of humans can be fully reused from ZED SDK. After that you can focus on prediction of humans.
- Make several input datasets (pictures, videos) with a ZED camera and use them as a repeatable and controlled experiment for comparing different approaches.
- Research the classic methods a little bit, eg how classic vision works for following a moving ball.
- Lidar is probably out of scope.

## 09.03.2026
Graduation Table Meeting 1: Planning and project organization
- You need to define measurable and testable acceptance criteria for the project to pass.
- Research horizontal and vertical slices as Agile approaches.
- An idea may be to try to make a environment simulation with multiple cameras (to make it 360 degrees or at least to have a wider field of view than just 1 camera).
- Talk with Edwin and Martin about setting up a controlled and repeatable experiment for the different approaches. Useful as a demo at the final presentation.
- For the next graduation table ask for feedback, have questions prepared (eg is my approach correct, what could be improved), show a demo, explain how you answered some of the research questions.
 
## 23.02.2026
- When presenting examples of point clouds generated using Depth Anything v3. the feedback was that it is nice because only 1 camera is needed to create a 3D map of the environment but it may be tricky and risky, for now it is unclear how deterministic the model is. Still, it is valuable to include it in the research.  
- ZED SDK (provided by the camera supplier) is probably more reliable than Depth Anything.  
- If available, check out Lidar or Lidar+RGB images.  
- Take a look at the Nvidia free online courses (e.g., autonomous robots, CUDA,...).

## 10.02.2026 - Intro
Went through the project proposal and discussed it.  
  
- Research:
	- Kalman filters (make a lot of sense for this project).
	- what is better: depth camera or Lidar sensor (maybe velocity can be estimated from Doppler effect).  
	- what is better: physics-based game engine (proven technology) or world models (new and less certain technology; maybe physics will be unrealistic and artifacts will exist).  
	- should the final product be a ROS2 program/node or something else.  

- Experiments:
	- Use real cameras, real input data in controlled environment. Do not use synthetic data only.  
	- Actual measurements will be needed.  
	- Simple high-school experiment can be developed - a ball falling down a ramp being tracked by a camera. Control camera (actual measurements) and test cameras (predictions) can be used for comparison.  

- Timeline:
	- Final portfolio delivery: Week 15.  
	- Assessment (do extra tasks if required by assessors): Week 16-17.
	- Official end of internship: July 10.  
	- Graduation ceremony: Week 21.
	- Weekly meetings: 13:30-14:00 on Mondays.

- Portfolio:
	- LO1 Professional Duties: the bulk of the work. More evidences expected compared to the other learning outcomes.  
	- Portfolio needs to be structured and readable. Make references between documents or different sections of the same document.  
	- Portfolio logical flow: analysis -> advice -> design -> implementation -> manage and control.
	- 1st portfolio submission: project plan made specifically for the project, not general key points valid for any project. Project plan will deviate from the actual project inevitably.

from pathlib import Path
import os, random, pandas as pd, uuid
from psychopy import visual, event, core, gui, data

PARTICIPANT_ID = uuid.uuid4()

win = visual.Window(color = 'black', fullscr = True, name = "Perception and action experiment")

# create a text stimulus
msg = visual.TextStim(win, text = 
  """
  Welcome to the experiment! 
  You will be presented with a series of photos. 
  If you believe the image has been modified by the experimenter, press 'j'. 
  If you believe the image is the original, press 'f'.
  
  Please respond as quickly as you can. 
  After 2 seconds the experiment will continue to the next image.
  
  Press any key to continue.
  """
)

msg.draw()
win.flip()

# wait for a key press
event.waitKeys()

# create a fixation cross
fixation = visual.TextStim(win, text = '+')
fixation.draw()
win.flip()
core.wait(1)

# get the pairs of images - they are named signal1.png, noise1.png, signal2.png, noise2.png, etc.
noise_images = list(Path('stimuli').rglob('noise*.jpg'))
signal_images = list(Path('stimuli').rglob('signal*.jpg'))

# make a list of 0s and 1s to randomly choose whether to show the signal or noise image, with exactly 50% probability
mask = [0, 1] * (len(noise_images) // 2)
random.shuffle(mask)

image_pairs = list(zip(signal_images, noise_images, mask))

# shuffle the order of the pairs
random.shuffle(image_pairs)

stopwatch = core.Clock()



image_trials = []
# for each of the pairs choose whether to show the signal or noise image
for trial_ID, (signal_image, noise_image, mask) in enumerate(image_pairs):
    fixation.draw()
    win.flip()
    core.wait(1)
    stopwatch.reset()
    
    # randomly choose whether to show the signal or noise image
    signal = bool(mask)
    print(signal_image if signal else noise_image)
    if (signal):
        image = visual.ImageStim(win, image = signal_image)
    else:
        image = visual.ImageStim(win, image = noise_image)

    image.draw()
    win.flip()
    
    # wait for a key press - f for noise, j for signal
    key_press = event.waitKeys(keyList = ['f', 'j', "escape"], maxWait = 2)

    # get the reaction time
    reaction_time = stopwatch.getTime()
      
    if (key_press is not None and key_press[0] == "escape"):
        win.close()
        core.quit()
        break
      
    if (key_press is None):
        response = "timeout"
    elif (key_press[0] == "f"):
        response = "noise"
    elif (key_press[0] == "j"):
        response = "signal"
    else:
        response = "error"
    
    # save the trial data
    image_trials.append({
        'subject_id': PARTICIPANT_ID,
        "trial_id": trial_ID,
        "stimuli_type": "signal" if signal else "noise",
        "stimuli": signal_image if signal else noise_image,
        "response": response,
        "reaction_time": reaction_time
    })
    
    # clear the screen
    win.flip()
    
print(image_trials)

def continue_experiment():
  visual.TextStim(win, text = 
    """
    You will now see a series of questions that you must answer yes/no to. 
    
    Press 'y' for yes and 'n' for no.
    Take as much time as you need.
    
    Press "y" or "j" to continue if you understand.
    """
    ).draw()
  win.flip()
  key_press = event.waitKeys(keyList = ['y', 'n', "f", "j", "escape"])
  if (key_press is None or key_press[0] == "escape"):
      win.close()
      core.quit()

  map_keys = {"f": "n", "j": "y"}
  if (key_press is not None and key_press[0] in map_keys):
      key_press[0] = map_keys[key_press[0]]

  if (key_press is not None and key_press[0] == "n"):
      continue_experiment()
  return

continue_experiment()


# Load the questions from a file
questions = pd.read_csv("questions.csv")

responses = {}

# get a list of the categories
categories = questions["category"].unique()
categories.sort()
for category in categories:
    if category not in responses:
        responses[category] = 0

# shuffle the order of the questions
questions = questions.sample(frac = 1)

        
for i, row in questions.iterrows():
  question, category = row["question"], row["category"]
  question_text = visual.TextStim(win, text = question)
  question_text.draw()
  win.flip()
  key_press = event.waitKeys(keyList = ['y', 'n', "f", "j", "escape"])
  if (key_press is None):
      continue
    
  if (key_press[0] == "escape"):
      win.close()
      core.quit()
      break
  
  map_keys = {"f": "n", "j": "y"}
  if (key_press is not None and key_press[0] in map_keys):
      key_press[0] = map_keys[key_press[0]]
  
  if (key_press[0] == "y"):
      responses[category] += 1
      
  win.flip()

win.close()

# Make a dialogue box to get participant info
dialog = gui.Dlg(title = "Perception and action exam")
dialog.addField("Age:")
dialog.addField("Gender: ", choices = ["Female", "Male", "Other"])
# dialog.addField("Education Level above primary school: ", choices = ["None", "High School", "Bachelors", "Masters", "PhD"])

# create a survey
dialog.addField("Time spent on social media per week (hours):", initial = "0")
dialog.addField("Time spent consuming news per week (hours):", initial = "0")
dialog.addField("Time spent creating visual content per week (hours):", initial = "0")
dialog.addField("Time spent fact-checking per week (hours):", initial = "0")


dialog.show()
      
if (dialog.OK):
    AGE = int(dialog.data[0])
    GENDER = dialog.data[1]
    # EDUCATION_LEVEL = dialog.data[2]
    SOCIAL_MEDIA_TIME = float(dialog.data[2])
    NEWS_TIME = float(dialog.data[3])
    CONTENT_CREATION_TIME = float(dialog.data[4])
    FACT_CHECKING_TIME = float(dialog.data[5])

# save the data from trials
trial_data_path = Path("./data/trial_data.csv")
trial_data = pd.DataFrame(image_trials)
trial_data.to_csv(trial_data_path, index = False, mode = "a", header=not trial_data_path.exists())

# concatenate the demographic data with the question responses
participant_data = pd.DataFrame({
    "subject_id": [PARTICIPANT_ID],
    "age": [AGE],
    "gender": [GENDER],
    # "education_level": [EDUCATION_LEVEL],
    "social_media_time": [SOCIAL_MEDIA_TIME],
    "news_time": [NEWS_TIME],
    "content_creation_time": [CONTENT_CREATION_TIME],
    "fact_checking_time": [FACT_CHECKING_TIME]
})

for category, response in responses.items():
    participant_data[category] = response

participant_data_path = Path("./data/participant_data.csv")
participant_data.to_csv(participant_data_path, index = False, mode = "a", header=not participant_data_path.exists())
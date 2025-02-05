import cozmo
import random
from src.base_logger import logger
from src.speech_detection import stream
from src.utils import say_text, check_answer_list, three_random_words
from src.speech_detection import confirmation_words, denial_words, skip_words, repeat_words
from src.animations import play_random_good_animation, play_random_bad_animation, fist_bump
from src.english.DictionaryEnglish import load_dictionary
from src.english.cozmo_initiation import cozmo_initiation
from src.threads import start_threads
from src.cubes import press_cube_to_speak

# Global variables relevant to all functions
name = ""
dictionary = load_dictionary()
dict_keys = list(dictionary.keys())
dict_length = len(dictionary)


# TODO: Tidy this up a bit, don't do two while loops for no reason other than laziness
# TODO: Skip the question or ask

def give_hint(robot, score, answer: str):
    logger.info("VOCAB: Giving hint... Score = {}".format(score))

    if score == -1:
        first_letter = answer[0]
        say_text("Here's a hint: the word begins with the letter, {}".format(first_letter), robot)

    elif score == -2:
        word_length = len(answer)
        words = [answer]

        if " " in answer:
            words = answer.split(" ")

        word_amount = len(words)

        if word_amount == 1:
            say_text("Here's another hint: the answer is a single word with {} letters.".format(word_length), robot)
        else:
            say_text("Here's another hint: the answer has {} words.".format(word_amount), robot)

    elif score <= -3:
        picked_words = three_random_words() + [answer]
        random.shuffle(picked_words)
        say_text("Which one of these words is the correct one?", robot)

        for answer in picked_words:
            say_text(answer, robot)


def definition_exercise(robot):
    logger.info("VOCAB: Start of vocabulary exercise...")
    # Initiate the dictionary and get the definitions + the length
    # say_text(
    #     "Today, we will do a vocabulary quiz. I will give you {} vocabulary questions that you need to answer".format(
    #         str(dict_length)),
    #     robot)
    # say_text("These words should be familiar to you from your class with Mr. Tommy Janota.", robot)
    # say_text("Ok, let's get started!", robot)
    try_again_flag = False
    counter = 0
    first_try_counter = 0
    score = 0

    stream.start_stream()

    while counter < dict_length:
        logger.info("VOCAB: In main loop, question {} of {}".format(counter, dict_length))
        correct = False
        first_try = True
        definition = dictionary.get(dict_keys[counter])[0]
        synonyms = dictionary.get(dict_keys[counter])[1]

        # The answer strings should have no spaces
        for i in range(synonyms):
            synonyms[i] = synonyms[i].replace(" ", "")

        word = dict_keys[counter]

        say_text("Question {}, {}".format(str(counter + 1), definition), robot)

        while not correct:

            text = press_cube_to_speak(robot)

            # If the user answers, then check if the answer is correct
            if text:

                logger.info("VOCAB: " + text)

                # If the user isn't sure about the question, cozmo asks if the user wants a hint or to skip the question

                # If the try_again_flag is set, make user stuck in the first part of the loop until he says yes or no
                if try_again_flag:

                    logger.info("VOCAB: User answering try_again...")

                    # Add long string of confirmation and denial words
                    if check_answer_list(text, confirmation_words):
                        print("in here")
                        try_again_flag = False
                        say_text("Question {}, {}".format(str(counter + 1), definition), robot)
                        score -= 1
                        give_hint(robot, score, word)

                    elif check_answer_list(text, denial_words):
                        print("in here")
                        try_again_flag = False
                        say_text("The word is {}.".format(word), robot)
                        say_text("It means {}".format(definition), robot)
                        break
                    else:
                        say_text("Can you repeat that? Please answer with, yes, or, no.", robot)
                    continue

                #The user can ask Cozmo to repeat the question.
                if check_answer_list(text, repeat_words):
                    say_text("Sure.", robot)
                    say_text("Question {}, {}".format(str(counter + 1), definition), robot)
                    continue

                if check_answer_list(text, skip_words):
                    try_again_flag = True
                    say_text("Do you want a clue?", robot)
                    say_text("Say, yes to get a clue, say, no to skip the question.", robot)
                    logger.info("VOCAB: User answering skip answer")
                    continue

                correct = check_answer_list(text.replace(" ", ""), synonyms)

                if correct:
                    logger.info("VOCAB: Correct answer: {} {}".format(text, word))
                    say_text("Your answer is correct, good job!", robot)
                    play_random_good_animation(robot)
                else:
                    logger.info("VOCAB: Incorrect answer: {} {}".format(text, word))
                    first_try = False
                    say_text("Your answer is not correct".format(text), robot)
                    play_random_bad_animation(robot)
                    try_again_flag = True
                    say_text("Would you like to try again?", robot)

        if first_try:
            first_try_counter += 1

        score = 0
        counter += 1
    stream.stop_stream()
    logger.info("VOCAB: End of vocabulary exercise...")
    return first_try_counter


def exercise_summary(first_try_counter, robot):
    logger.info("VOCAB: Start of vocabulary exercise summary...")
    score = first_try_counter / dict_length
    percentage = score * 100
    percentage = round(percentage, 2)
    logger.info("VOCAB: {} = {}/{}".format(float(percentage), int(dict_length), int(first_try_counter)))
    say_text("I would like to say, first of all, great job, {}".format(name), robot)
    say_text("Give me a nice fist bump!", robot)
    logger.info("VOCAB: Starting fist bump...")
    fist_bump(robot)
    logger.info("VOCAB: Ending fist bump...")
    say_text("You got {} correct answers out of {} questions. That is a {} percentage.".format(first_try_counter,
                                                                                               dict_length,
                                                                                               percentage), robot)
    if percentage >= 70:
        say_text("Fantastic job! I'm impressed!", robot)
    elif percentage >= 50:
        say_text("Good job! That was good!", robot)
    elif percentage >= 30:
        say_text("You are getting there. Don't give up and let's keep practicing!", robot)
    else:
        say_text(
            "It's not that easy, but I'm glad that you are trying, don't give up and let's practice again next "
            "time!", robot)
    play_random_good_animation(robot)
    logger.info("End of vocabulary exercise summary...")


def cozmo_vocabulary(robot: cozmo.robot.Robot):
    try:
        global name
        name = cozmo_initiation(robot)

        first_try_counter = definition_exercise(robot)
        exercise_summary(first_try_counter, robot)

    except Exception as e:
        logger.critical(e, exc_info=True)


def main(robot: cozmo.robot.Robot):
    # This condition is used to stop the thread looping in follow_face
    start_threads(robot, cozmo_vocabulary)


if __name__ == "__main__":
    cozmo.run_program(main)

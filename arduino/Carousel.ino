#include "Arduino.h"
#include "AccelStepper.h"
#include "Constants.h"
#include "Config.h"


#define MICROSTEPPING_FACTOR  4
#define FULL_STEPS_PER_REV     2520
#define FULL_ROTATION_STEPS    (FULL_STEPS_PER_REV * MICROSTEPPING_FACTOR)
#define CUVE_PER_SLOT          12
#define SLOT_COUNT             6
#define SLOT_SPACING_STEPS     420  // Between slots (in full steps)
#define CUVE_SPACING_STEPS     30   // Between cuvettes within slot (in full steps)
#define INIT_OFFSET  0  // Between the home sensor position and centre of the first cuvette
#define MAX_INIT_POSITION      11000


int initializeCarousel() {

    if (digitalRead(DOOR_PIN) == HIGH) {
    Serial.println("Unable to initialize carousel. Door is open.");
    return (4); // Door open
  }

    unsigned int vdrop=analogRead(HOME_SENSOR_POWER_PIN);
  if (vdrop < 200){
    Serial.print("Position sensor malfunction! Current too high! ADC0 value:");
    Serial.println(vdrop);
    carouselInitialized = false;
    return(2); // Sensor current too high

  } else if(vdrop > 400){
    Serial.print("Position sensor malfunction! Current too low! ADC0 value:");
    Serial.println(vdrop);
    carouselInitialized = false;
    return(3); // Sensor current too low
  }

  if (digitalRead(HOME_SENSOR_PIN) == HIGH) {
    stepper.moveTo(500);
    stepper.runToPosition();
    if (digitalRead(HOME_SENSOR_PIN) == HIGH) {
      Serial.println(F("Unable to initialize carousel! Motor stuck on home position"));
      carouselInitialized = false;
      return(5); // Motor jammed on home position
  }
}

  stepper.setSpeed(-500);

  while (true) {
    stepper.runSpeed();

    if (stepper.currentPosition() < -MAX_INIT_POSITION) {
      stepper.setSpeed(0);
      Serial.println(F("Unable to initialize carousel!"));
      carouselInitialized = false;
      return 1;  // Failure
    }

    if (digitalRead(HOME_SENSOR_PIN) == HIGH) {  // Sensor active
      stepper.setSpeed(0);
      stepper.setCurrentPosition(INIT_OFFSET);
      Serial.println(F("Carousel initialized."));
      carouselInitialized = true;
      return 0;  // Success
    }
  }
}

void moveToCuvette(int index) {

  if (digitalRead(DOOR_PIN) == HIGH) {
    Serial.println("Door is open.");
    return;
  }

  if (!carouselInitialized) {
    Serial.println("Carousel not initialized!");
    return;
  }

  long targetSteps = getCarouselPosition(index-1) * MICROSTEPPING_FACTOR;

  long normCurrent = ((currentStepPosition % FULL_ROTATION_STEPS) + FULL_ROTATION_STEPS) % FULL_ROTATION_STEPS;
  long normTarget = ((targetSteps % FULL_ROTATION_STEPS) + FULL_ROTATION_STEPS) % FULL_ROTATION_STEPS;

  long delta = normTarget - normCurrent;

  if (delta > FULL_ROTATION_STEPS / 2) {
    delta -= FULL_ROTATION_STEPS;
  } else if (delta < -FULL_ROTATION_STEPS / 2) {
    delta += FULL_ROTATION_STEPS;
  }

  stepper.move(delta);
  stepper.runToPosition();

  currentStepPosition += delta;
  Serial.println(F("OK"));
}

void moveToSlot(int slot) {
  Serial.println(F("OK"));
}

void moveToStep(int step) {

  if (digitalRead(DOOR_PIN) == HIGH) {
    Serial.println("Door is open.");
    return;
  }

  if (!carouselInitialized) {
    Serial.println("Carousel not initialized!");
    return;
  }

  stepper.moveTo(step);
  stepper.runToPosition();
  Serial.println(F("OK"));
}


int getCarouselPosition(int index) {

  if (digitalRead(DOOR_PIN) == HIGH) {
    Serial.println("Door is open.");
    return(0);
  }

  if (!carouselInitialized) {
    Serial.println("Carousel not initialized!");
    return(0);
  }

  int slot = index / CUVE_PER_SLOT;
  int offset = index % CUVE_PER_SLOT;
  return (slot * SLOT_SPACING_STEPS) + (offset * CUVE_SPACING_STEPS);
}

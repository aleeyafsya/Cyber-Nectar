#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// --- PIN DEFINITIONS ---
const int redLedPin = 5;      // GPIO 5 (D5) - CRITICAL
const int yellowLedPin = 4;   // GPIO 4 (D4) - MEDIUM
const int buzzerPin = 18;     // GPIO 18 (D18)

// --- LCD CONFIGURATION ---
LiquidCrystal_I2C lcd(0x27, 16, 2); 

void setup() {
  // Use a fast baud rate for instant response
  Serial.begin(115200);
  
  pinMode(redLedPin, OUTPUT);
  pinMode(yellowLedPin, OUTPUT);
  pinMode(buzzerPin, OUTPUT);
  
  digitalWrite(redLedPin, LOW);
  digitalWrite(yellowLedPin, LOW);
  digitalWrite(buzzerPin, LOW);

  lcd.init();
  lcd.backlight();
  lcd.display();
  lcd.clear();
  showNormalState();
  
  Serial.println("ESP32 Serial Bridge Ready.");
}

void loop() {
  // Check for Serial commands from the PC (Relay Script)
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 
    
    if (command == "CRITICAL") {
      triggerCritical();
    } else if (command == "MEDIUM") {
      triggerMedium();
    } else if (command == "NORMAL") {
      showNormalState();
    }
  }
}

void triggerCritical() {
  digitalWrite(redLedPin, HIGH);
  digitalWrite(yellowLedPin, LOW);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("!! CRITICAL !!");
  lcd.setCursor(0, 1);
  lcd.print("ATTACK DETECTED");
  
  // Alert sound
  for(int i = 0; i < 3; i++) {
    digitalWrite(buzzerPin, HIGH);
    delay(100);
    digitalWrite(buzzerPin, LOW);
    delay(100);
  }
}

void triggerMedium() {
  digitalWrite(redLedPin, LOW);
  digitalWrite(yellowLedPin, HIGH);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("WARNING:");
  lcd.setCursor(0, 1);
  lcd.print("Medium Threat");
  
  digitalWrite(buzzerPin, HIGH);
  delay(300);
  digitalWrite(buzzerPin, LOW);
}

void showNormalState() {
  digitalWrite(redLedPin, LOW);
  digitalWrite(yellowLedPin, LOW);
  
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Honeypot Active");
  lcd.setCursor(3, 1);
  lcd.print("SECURED");
}
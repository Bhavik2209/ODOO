class PHQ9Assessment:
    def __init__(self):
        self.questions = [
            "Little interest or pleasure in doing things",
            "Feeling down, depressed, or hopeless",
            "Trouble falling or staying asleep, or sleeping too much",
            "Feeling tired or having little energy",
            "Poor appetite or overeating",
            "Feeling bad about yourself or that you are a failure or have let yourself or your family down",
            "Trouble concentrating on things, such as reading the newspaper or watching television",
            "Moving or speaking so slowly that other people could have noticed. Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual",
            "Thoughts that you would be better off dead, or of hurting yourself"
        ]
        
        self.frequency_options = {
            0: "Not at all",
            1: "Several days",
            2: "More than half the days",
            3: "Nearly every day"
        }
        
        self.difficulty_levels = [
            "Not difficult at all",
            "Somewhat difficult",
            "Very difficult",
            "Extremely difficult"
        ]
        
        self.severity_levels = {
            range(0, 5): "Minimal depression",
            range(5, 10): "Mild depression",
            range(10, 15): "Moderate depression",
            range(15, 20): "Moderately severe depression",
            range(20, 28): "Severe depression"
        }
        
        self.responses = []
        self.difficulty_response = None

    def conduct_assessment(self):
        """Conducts the PHQ-9 assessment interactively."""
        print("\nPATIENT HEALTH QUESTIONNAIRE (PHQ-9)")
        print("\nOver the last 2 weeks, how often have you been bothered by any of the following problems?")
        print("\nScoring options:")
        for score, desc in self.frequency_options.items():
            print(f"{score}: {desc}")

        self.responses = []
        
        for i, question in enumerate(self.questions, 1):
            while True:
                try:
                    print(f"\n{i}. {question}")
                    response = int(input("Enter your score (0-3): "))
                    if response in self.frequency_options:
                        self.responses.append(response)
                        break
                    else:
                        print("Please enter a valid score (0-3)")
                except ValueError:
                    print("Please enter a valid number")

        print("\nIf you checked off any problems, how difficult have these problems made it for")
        print("you to do your work, take care of things at home, or get along with other people?")
        
        for i, level in enumerate(self.difficulty_levels):
            print(f"{i}: {level}")
            
        while True:
            try:
                difficulty = int(input("\nEnter difficulty level (0-3): "))
                if difficulty in range(len(self.difficulty_levels)):
                    self.difficulty_response = difficulty
                    break
                else:
                    print("Please enter a valid difficulty level (0-3)")
            except ValueError:
                print("Please enter a valid number")

    def calculate_score(self):
        """Calculates the total score and returns diagnostic information."""
        total_score = sum(self.responses)
        
        # Determine severity level
        severity = None
        for score_range, level in self.severity_levels.items():
            if total_score in score_range:
                severity = level
        
        # Check for Major Depressive Disorder criteria
        count_of_threes = sum(1 for score in self.responses if score == 3)
        has_core_symptoms = self.responses[0] == 3 or self.responses[1] == 3  # Questions 1 or 2
        
        major_depression_criteria = count_of_threes >= 5 and has_core_symptoms
        other_depression_criteria = (2 <= count_of_threes <= 4) and has_core_symptoms
        
        return {
            'total_score': total_score,
            'severity': severity,
            'responses': self.responses,
            'difficulty_level': self.difficulty_levels[self.difficulty_response],
            'potential_major_depression': major_depression_criteria,
            'potential_other_depression': other_depression_criteria
        }

    def generate_report(self):
        """Generates a detailed report of the assessment."""
        results = self.calculate_score()
        
        report = "\nPHQ-9 Assessment Report"
        report += "\n" + "="*50
        
        report += f"\n\nTotal Score: {results['total_score']}"
        report += f"\nSeverity Level: {results['severity']}"
        report += f"\nFunctional Difficulty: {results['difficulty_level']}"
        
        report += "\n\nDetailed Responses:"
        for i, (question, response) in enumerate(zip(self.questions, results['responses']), 1):
            report += f"\n{i}. {question}"
            report += f"\n   Response: {self.frequency_options[response]}"
        
        report += "\n\nClinical Considerations:"
        if results['potential_major_depression']:
            report += "\n- Consider Major Depressive Disorder"
            report += "\n  (5 or more symptoms at 'Nearly every day' including at least one core symptom)"
        elif results['potential_other_depression']:
            report += "\n- Consider Other Depressive Disorder"
            report += "\n  (2-4 symptoms at 'Nearly every day' including at least one core symptom)"
        
        report += "\n\nNote: This questionnaire is a screening tool. A definitive diagnosis"
        report += "\nshould be made by a qualified healthcare professional taking into"
        report += "\naccount clinical observation and other relevant information."
        
        return report

def main():
    assessment = PHQ9Assessment()
    assessment.conduct_assessment()
    print(assessment.generate_report())

if __name__ == "__main__":
    main()
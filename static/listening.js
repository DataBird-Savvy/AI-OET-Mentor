
const tasks = `{{ task_question | safe }}`|| null;  
const next_got=`{{ next_got | tojson | safe }}`;
const audioUrl = `{{ audio_file | safe }}`|| null;
const timeAllotted = parseInt(`{{time_allowed}}`|| null);
const feedback = `{{ feedback | safe }}`|| null; 
const feedbackgot = `{{ feedback_got | tojson | safe }}`;
const filtered_B = `{{ filtered_B | tojson | safe }}`;

console.log(tasks)
console.log(next_got)
console.log(timeAllotted)
console.log(audioUrl)
console.log(feedback)
console.log(feedbackgot)
console.log(filtered_B)



let timeLimit = timeAllotted * 60;  // Convert minutes to seconds
let timer;  // To hold the countdown timer
let timeRemaining = timeLimit;  // Initialize with time limit

document.getElementById('audioSource').src = audioUrl;
function startTest() {
    // Show the test content and hide the start button
    document.getElementById('test-content').style.display = 'block';
    document.getElementById('start-button').style.display = 'none';
    document.querySelector('.feedback-box').style.display = 'none';
    document.getElementById('timer-display').style.display = 'block';
    document.getElementById('tips-container').style.display = 'none';
    
    
    // Load tasks and reset the timer
    loadAllTasks(tasks);
    displayQuestions(filtered_B);
    timeRemaining = timeLimit;  // Reset time
    updateTimerDisplay();  // Update timer initially
    startCountdown();  // Start countdown timer
}





function loadAllTasks(tasks) {
  document.getElementById('tips-container').style.display = 'none';
  const taskContainer = document.getElementById('task-question');
  taskContainer.innerHTML = ''; 
  const taskArray = tasks.split('\n\n');
  let k = 0; 

  taskArray.forEach((task, index) => {
      
      const taskWithInputs = task.replace(/____/g, () => {
          return `<input type="text" name="answer${k++}" placeholder="" />`;
      });

      // Create a div to hold each task's content
      const taskDiv = document.createElement('div');
      taskDiv.innerHTML = marked(taskWithInputs); // Assuming 'marked' is used for Markdown parsing
      taskDiv.style.marginBottom = '20px';

      // Append the task div to the main task container
      taskContainer.appendChild(taskDiv);
  });
  
  
  
}



function gatherAndSubmitAnswers(event) {
event.preventDefault(); // Prevent default form submission
document.querySelector('.feedback-box').style.display = 'block';
document.getElementById('test-content').style.display = 'block';
document.getElementById('start-button').style.display = 'none';
document.getElementById('timer-display').style.display = 'none';
document.getElementById('tips-container').style.display = 'none';

// Collect answers from input fields
const inputs = document.querySelectorAll('#task-question input[type="text"]');
const answers = Array.from(inputs).map(input => input.value);

// Prepare the payload
const payload = {
  answers: answers,
  task: tasks, // Ensure this is defined elsewhere
  audioUrl: audioUrl // Ensure this is defined elsewhere
};

// Send the payload to the backend using Fetch API
fetch('/listening_task', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(payload),
})
  .then(response => response.json())
  .then(data => {
    console.log('Submission successful:', data);

    // Handle successful response (e.g., update feedback)
    if (data.feedback) {
      document.getElementById('feedback-display').innerHTML = marked(data.feedback);
    }
  })
  .catch(error => {
    console.error('Error during submission:', error);
    // Handle error response (e.g., display an error message)
  });
}


function updateTimerDisplay() {
    const minutes = Math.floor(timeRemaining / 60);
    const seconds = timeRemaining % 60;
    document.getElementById('timer-display').textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
}

function displayQuestionsFromJson(jsonData) {
    console.log('Displaying questions...', jsonData);
    const container = document.getElementById('questions-container');

    if (!container) {
        console.error('questions-container element not found in the DOM.');
        return;
    }

    container.style.display = 'block';
    container.innerHTML = ''; // Clear previous questions

    const instructionText = jsonData["part B"].instruction || "Follow the instructions to answer the questions.";
    const instructions = document.createElement('p');
    instructions.textContent = instructionText;
    container.appendChild(instructions);

    const mcqs = jsonData["part B"].MCQ_25_30;

    if (!mcqs || mcqs.length === 0) {
        console.error('No questions found in jsonData["part B"].MCQ_25_30');
        return;
    }

    mcqs.forEach(questionObj => {
        const questionNumber = Object.keys(questionObj)[0];
        const questionDetails = questionObj[questionNumber];
        const questionText = questionDetails.text;
        const options = questionDetails.options;

        const questionDiv = document.createElement('div');
        questionDiv.classList.add('question');

        const questionTitle = document.createElement('h3');
        questionTitle.textContent = `${questionNumber}. ${questionText}`;
        questionDiv.appendChild(questionTitle);

        const optionsList = document.createElement('ul');
        options.forEach((option, index) => {
            const optionItem = document.createElement('li');
            const radioInput = document.createElement('input');
            radioInput.type = 'radio';
            radioInput.name = `question${questionNumber}`;
            radioInput.id = `q${questionNumber}_opt${index}`;
            radioInput.value = option;

            const label = document.createElement('label');
            label.htmlFor = `q${questionNumber}_opt${index}`;
            label.textContent = option;

            optionItem.appendChild(radioInput);
            optionItem.appendChild(label);
            optionsList.appendChild(optionItem);
        });

        questionDiv.appendChild(optionsList);
        container.appendChild(questionDiv);
    });
}

  


function startCountdown() {
    timer = setInterval(() => {
        timeRemaining--;
        updateTimerDisplay();
        
        if (timeRemaining <= 0) {
            clearInterval(timer);
            document.getElementById('feedback-section').style.display = 'block';
            document.getElementById('feedback-message').textContent = "Time's up! Please submit your task.";
            // Optionally, you can automatically submit the form
            // document.getElementById('letter-form').submit();
        }
    }, 1000); // Update every second
}

// Ensure the page behaves according to whether the test has started or not
window.onload = function() {

  
    if (next_got === 'true'){
      startTest()

    }

};
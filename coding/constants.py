# Difficulty Levels
DIFFICULTY_EASY = 'Easy'
DIFFICULTY_MEDIUM = 'Medium'
DIFFICULTY_HARD = 'Hard'

DIFFICULTY_CHOICES = [
    (DIFFICULTY_EASY, 'Easy'),
    (DIFFICULTY_MEDIUM, 'Medium'),
    (DIFFICULTY_HARD, 'Hard'),
]

# Submission Compile/Execution Statuses
STATUS_ACCEPTED = 'Accepted'
STATUS_WRONG_ANSWER = 'Wrong Answer'
STATUS_RUNTIME_ERROR = 'Runtime Error'
STATUS_COMPILATION_ERROR = 'Compilation Error'
STATUS_TIME_LIMIT_EXCEEDED = 'Time Limit Exceeded'
STATUS_MEMORY_LIMIT_EXCEEDED = 'Memory Limit Exceeded'
STATUS_PENDING = 'Pending'
STATUS_SUBMITTED = 'Submitted'

SUBMISSION_STATUS_CHOICES = [
    (STATUS_ACCEPTED, 'Accepted'),
    (STATUS_WRONG_ANSWER, 'Wrong Answer'),
    (STATUS_RUNTIME_ERROR, 'Runtime Error'),
    (STATUS_COMPILATION_ERROR, 'Compilation Error'),
    (STATUS_TIME_LIMIT_EXCEEDED, 'Time Limit Exceeded'),
    (STATUS_MEMORY_LIMIT_EXCEEDED, 'Memory Limit Exceeded'),
    (STATUS_PENDING, 'Pending'),
    (STATUS_SUBMITTED, 'Submitted'),
]

# Supported Programming Languages
LANG_PYTHON = 'Python'
LANG_JAVASCRIPT = 'JavaScript'
LANG_JAVA = 'Java'
LANG_CPP = 'C++'
LANG_SQL = 'SQL'
LANG_GO = 'Go'
LANG_RUST = 'Rust'

PROGRAMMING_LANGUAGE_CHOICES = [
    (LANG_PYTHON, 'Python'),
    (LANG_JAVASCRIPT, 'JavaScript'),
    (LANG_JAVA, 'Java'),
    (LANG_CPP, 'C++'),
    (LANG_SQL, 'SQL'),
    (LANG_GO, 'Go'),
    (LANG_RUST, 'Rust'),
]

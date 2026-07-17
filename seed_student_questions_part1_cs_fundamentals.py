"""
Student-Focused Interview Questions - Part 1: CS Fundamentals
For campus placements and entry-level roles
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from questions.models import QuestionCategory, Topic, InterviewQuestion
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first() or User.objects.first()

# Create/Get Categories
dsa_cat, _ = QuestionCategory.objects.get_or_create(name='DSA', defaults={'icon': 'Code', 'display_order': 8})
os_cat, _ = QuestionCategory.objects.get_or_create(name='OS', defaults={'icon': 'Cpu', 'display_order': 5})
dbms_cat, _ = QuestionCategory.objects.get_or_create(name='DBMS', defaults={'icon': 'Database', 'display_order': 4})
oop_cat, _ = QuestionCategory.objects.get_or_create(name='OOP', defaults={'icon': 'Box', 'display_order': 7})
networking_cat, _ = QuestionCategory.objects.get_or_create(name='Networking', defaults={'icon': 'Globe', 'display_order': 6})

# Create Topics for DSA
dsa_topics = {
    'Arrays & Strings': 'Basic array operations, string manipulation, two-pointer techniques',
    'Linked Lists': 'Singly, doubly linked lists, insertion, deletion, reversal',
    'Stacks & Queues': 'LIFO, FIFO operations, implementation, applications',
    'Trees & BST': 'Binary trees, BST operations, traversals, height, depth',
    'Hashing': 'Hash tables, collision handling, applications',
    'Sorting & Searching': 'Bubble, insertion, merge, quick sort, binary search',
    'Recursion': 'Base case, recursive case, backtracking basics',
    'Time Complexity': 'Big O notation, space complexity analysis'
}

topics_map = {}
for topic_name, desc in dsa_topics.items():
    t, _ = Topic.objects.get_or_create(category=dsa_cat, name=topic_name, defaults={'description': desc})
    topics_map[topic_name] = t

# Create Topics for OS
os_topics = {
    'Process Management': 'Process states, PCB, scheduling algorithms',
    'Threads': 'Process vs thread, multithreading, concurrency',
    'Memory Management': 'Paging, segmentation, virtual memory',
    'Deadlock': 'Conditions, prevention, avoidance, detection'
}
for topic_name, desc in os_topics.items():
    t, _ = Topic.objects.get_or_create(category=os_cat, name=topic_name, defaults={'description': desc})
    topics_map[topic_name] = t

# Create Topics for DBMS
dbms_topics = {
    'Normalization': '1NF, 2NF, 3NF, BCNF forms',
    'SQL Basics': 'SELECT, JOIN, GROUP BY, aggregate functions',
    'Transactions': 'ACID properties, isolation levels',
    'Indexing': 'B-tree, B+ tree, primary vs secondary index'
}
for topic_name, desc in dbms_topics.items():
    t, _ = Topic.objects.get_or_create(category=dbms_cat, name=topic_name, defaults={'description': desc})
    topics_map[topic_name] = t

# Create Topics for OOP
oop_topics = {
    'OOP Principles': 'Encapsulation, inheritance, polymorphism, abstraction',
    'Classes & Objects': 'Constructor, destructor, instance vs class variables',
    'Inheritance': 'Single, multiple, multilevel, hierarchical',
    'Polymorphism': 'Compile-time vs runtime, method overloading vs overriding'
}
for topic_name, desc in oop_topics.items():
    t, _ = Topic.objects.get_or_create(category=oop_cat, name=topic_name, defaults={'description': desc})
    topics_map[topic_name] = t

# Create Topics for Networking
net_topics = {
    'OSI Model': '7 layers, functions, protocols at each layer',
    'TCP/IP': 'TCP vs UDP, 3-way handshake, connection management',
    'HTTP Basics': 'Methods, status codes, request/response structure',
    'Network Security': 'Encryption, SSL/TLS, firewalls basics'
}
for topic_name, desc in net_topics.items():
    t, _ = Topic.objects.get_or_create(category=networking_cat, name=topic_name, defaults={'description': desc})
    topics_map[topic_name] = t

# ============================================================================
# DSA QUESTIONS (Student Level)
# ============================================================================

dsa_questions = [
    # Arrays & Strings - Easy
    {
        'question': 'How do you find the largest element in an array? Write the approach and explain the time complexity.',
        'short_description': 'Find largest element in array',
        'category': dsa_cat,
        'topic': topics_map['Arrays & Strings'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Text',
        'tags': ['Arrays', 'Basic', 'Traversal'],
        'hints': ['Iterate through the array once', 'Keep track of maximum value', 'Time complexity is O(n)'],
        'expected_answer': 'Initialize a variable max with the first element. Traverse the array and update max whenever a larger element is found. Return max at the end. Time Complexity: O(n), Space Complexity: O(1).',
        'explanation': 'This is a basic traversal problem testing understanding of array iteration and variable tracking.'
    },
    {
        'question': 'Explain how to reverse a string in-place. What are the edge cases you need to handle?',
        'short_description': 'Reverse string in-place',
        'category': dsa_cat,
        'topic': topics_map['Arrays & Strings'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Text',
        'tags': ['Strings', 'Two Pointers', 'In-place'],
        'hints': ['Use two pointers from start and end', 'Swap characters', 'Edge cases: empty string, single character'],
        'expected_answer': 'Use two pointers, one at start (i=0) and one at end (j=n-1). Swap characters at i and j, increment i, decrement j until i >= j. Edge cases: null string, empty string, single character. Time: O(n), Space: O(1).',
        'explanation': 'Tests understanding of two-pointer technique and edge case handling.'
    },
    {
        'question': 'What is the two-pointer technique? Explain with an example of finding a pair with given sum in a sorted array.',
        'short_description': 'Two-pointer technique for pair sum',
        'category': dsa_cat,
        'topic': topics_map['Arrays & Strings'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Two Pointers', 'Arrays', 'Sorted'],
        'hints': ['One pointer at start, one at end', 'Move pointers based on sum comparison', 'Works on sorted arrays'],
        'expected_answer': 'Two-pointer uses two indices to traverse from opposite ends. For pair sum: left=0, right=n-1. If arr[left]+arr[right]==target, return pair. If sum<target, left++. If sum>target, right--. Time: O(n), Space: O(1).',
        'explanation': 'Fundamental technique for array problems, especially on sorted arrays.'
    },
    
    # Linked Lists - Easy/Medium
    {
        'question': 'What is the difference between an array and a linked list? When would you prefer one over the other?',
        'short_description': 'Array vs Linked List comparison',
        'category': dsa_cat,
        'topic': topics_map['Linked Lists'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Linked List', 'Arrays', 'Comparison', 'Fundamentals'],
        'hints': ['Memory allocation differences', 'Access time differences', 'Insertion/deletion efficiency'],
        'expected_answer': 'Arrays: Contiguous memory, O(1) random access, fixed size (or resize overhead), O(n) insertion/deletion. Linked Lists: Non-contiguous memory, O(n) access, dynamic size, O(1) insertion/deletion at known position. Use arrays for frequent access, linked lists for frequent insertions/deletions.',
        'explanation': 'Fundamental data structure comparison question common in campus placements.'
    },
    {
        'question': 'How do you detect a cycle in a linked list? Explain the Floyd\'s Cycle Detection algorithm.',
        'short_description': 'Detect cycle in linked list',
        'category': dsa_cat,
        'topic': topics_map['Linked Lists'],
        'difficulty': 'Medium',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Linked List', 'Cycle Detection', 'Two Pointers', 'Floyd Algorithm'],
        'hints': ['Use slow and fast pointers', 'Slow moves 1 step, fast moves 2 steps', 'If they meet, cycle exists'],
        'expected_answer': 'Floyd\'s algorithm uses two pointers: slow (moves 1 step) and fast (moves 2 steps). Start both at head. If fast reaches NULL, no cycle. If slow==fast at any point, cycle exists. Time: O(n), Space: O(1).',
        'explanation': 'Classic linked list problem testing understanding of pointer manipulation and cycle detection.'
    },
    {
        'question': 'Write the approach to reverse a singly linked list. Can you do it iteratively and recursively?',
        'short_description': 'Reverse a singly linked list',
        'category': dsa_cat,
        'topic': topics_map['Linked Lists'],
        'difficulty': 'Easy',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Linked List', 'Reversal', 'Iteration', 'Recursion'],
        'hints': ['Iterative: Use three pointers prev, curr, next', 'Recursive: Reverse from second node, then fix links', 'Change next pointers direction'],
        'expected_answer': 'Iterative: Use prev=NULL, curr=head. While curr: next=curr.next; curr.next=prev; prev=curr; curr=next. Return prev. Recursive: Reverse rest of list, then fix head.next.next=head; head.next=NULL. Time: O(n), Space: O(1) iterative, O(n) recursive stack.',
        'explanation': 'Fundamental linked list manipulation problem, tests pointer handling skills.'
    },
    
    # Stacks & Queues - Easy
    {
        'question': 'Explain the difference between Stack and Queue. Give real-world examples of each.',
        'short_description': 'Stack vs Queue with examples',
        'category': dsa_cat,
        'topic': topics_map['Stacks & Queues'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Text',
        'tags': ['Stack', 'Queue', 'LIFO', 'FIFO', 'Fundamentals'],
        'hints': ['Stack is LIFO', 'Queue is FIFO', 'Think of plates vs ticket counter'],
        'expected_answer': 'Stack: LIFO (Last In First Out) - like a stack of plates. Push and pop from same end. Examples: Browser back button, function call stack, undo operations. Queue: FIFO (First In First Out) - like a ticket counter line. Enqueue at rear, dequeue from front. Examples: Print queue, BFS traversal, CPU scheduling.',
        'explanation': 'Basic data structure concepts essential for campus placements.'
    },
    {
        'question': 'How can you implement a queue using two stacks? Explain the approach and time complexity.',
        'short_description': 'Implement queue using two stacks',
        'category': dsa_cat,
        'topic': topics_map['Stacks & Queues'],
        'difficulty': 'Medium',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Stack', 'Queue', 'Implementation', 'Design'],
        'hints': ['Use one stack for enqueue, one for dequeue', 'Transfer elements when dequeue stack is empty', 'Amortized O(1) operations'],
        'expected_answer': 'Use two stacks: stack1 (for enqueue) and stack2 (for dequeue). Enqueue: Push to stack1 - O(1). Dequeue: If stack2 empty, pop all from stack1 and push to stack2. Then pop from stack2. Amortized time: O(1) for both operations.',
        'explanation': 'Tests understanding of how different data structures can be combined creatively.'
    },
    {
        'question': 'What are the applications of Stack in real-world programming? Name at least three.',
        'short_description': 'Real-world stack applications',
        'category': dsa_cat,
        'topic': topics_map['Stacks & Queues'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Text',
        'tags': ['Stack', 'Applications', 'Practical'],
        'hints': ['Think about recursion', 'Expression evaluation', 'Browser functionality'],
        'expected_answer': '1. Function call management (call stack) - stores return addresses and local variables. 2. Expression evaluation - infix to postfix conversion, parenthesis matching. 3. Backtracking algorithms - maze solving, N-Queens. 4. Browser back/forward navigation. 5. Undo/Redo functionality in editors.',
        'explanation': 'Understanding practical applications shows depth of knowledge beyond just theory.'
    },
    
    # Trees - Easy/Medium
    {
        'question': 'What is a Binary Tree? How is it different from a Binary Search Tree (BST)?',
        'short_description': 'Binary Tree vs BST',
        'category': dsa_cat,
        'topic': topics_map['Trees & BST'],
        'difficulty': 'Easy',
        'expected_duration': 3,
        'answer_type': 'Text',
        'tags': ['Trees', 'BST', 'Fundamentals'],
        'hints': ['Binary tree has max 2 children', 'BST has ordering property', 'BST allows efficient search'],
        'expected_answer': 'Binary Tree: Each node has at most 2 children (left and right). No ordering constraint. BST (Binary Search Tree): Binary tree with ordering - left subtree has smaller values, right subtree has larger values. BST enables O(log n) search, insert, delete in balanced tree.',
        'explanation': 'Fundamental tree concept tested in almost all campus placements.'
    },
    {
        'question': 'Explain the three types of tree traversal: Inorder, Preorder, and Postorder with examples.',
        'short_description': 'Tree traversal types',
        'category': dsa_cat,
        'topic': topics_map['Trees & BST'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Trees', 'Traversal', 'Recursion'],
        'hints': ['Inorder: Left-Root-Right', 'Preorder: Root-Left-Right', 'Postorder: Left-Right-Root'],
        'expected_answer': 'Inorder (Left-Root-Right): Visits left subtree, then root, then right. In BST gives sorted order. Preorder (Root-Left-Right): Visits root first, then left, then right. Used for tree copying. Postorder (Left-Right-Root): Visits both children before root. Used for tree deletion.',
        'explanation': 'Basic tree traversal is essential for any tree-related problem.'
    },
    {
        'question': 'How do you find the height of a binary tree? Write the recursive approach.',
        'short_description': 'Find height of binary tree',
        'category': dsa_cat,
        'topic': topics_map['Trees & BST'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Trees', 'Height', 'Recursion'],
        'hints': ['Base case: NULL node has height 0 or -1', 'Recursive case: 1 + max of left and right heights', 'Height = longest path from root to leaf'],
        'expected_answer': 'Recursive approach: height(node) { if node==NULL return 0; leftHeight = height(node.left); rightHeight = height(node.right); return 1 + max(leftHeight, rightHeight); }. Time: O(n), Space: O(h) for recursion stack where h is height.',
        'explanation': 'Classic recursion problem on trees, tests understanding of tree properties.'
    },
    
    # Sorting & Searching - Easy/Medium
    {
        'question': 'Explain how Binary Search works. Why does the array need to be sorted?',
        'short_description': 'Binary Search explanation',
        'category': dsa_cat,
        'topic': topics_map['Sorting & Searching'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Binary Search', 'Searching', 'Sorted Array'],
        'hints': ['Divide and conquer approach', 'Compare with middle element', 'Halve search space each time'],
        'expected_answer': 'Binary Search repeatedly divides sorted array in half. Compare target with middle element. If equal, found. If target<middle, search left half. If target>middle, search right half. Array must be sorted to determine which half contains target. Time: O(log n), Space: O(1) iterative.',
        'explanation': 'Fundamental search algorithm, prerequisite for many advanced problems.'
    },
    {
        'question': 'Compare Bubble Sort and Merge Sort. Which is better and why?',
        'short_description': 'Bubble Sort vs Merge Sort',
        'category': dsa_cat,
        'topic': topics_map['Sorting & Searching'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Sorting', 'Bubble Sort', 'Merge Sort', 'Comparison'],
        'hints': ['Compare time complexities', 'Bubble sort is simple but slow', 'Merge sort uses divide and conquer'],
        'expected_answer': 'Bubble Sort: O(n²) time, O(1) space, stable, in-place. Simple but inefficient for large data. Repeatedly swaps adjacent elements. Merge Sort: O(n log n) time, O(n) space, stable, divide-and-conquer. Divides array, sorts halves, merges. Merge Sort is better for large datasets due to superior time complexity.',
        'explanation': 'Understanding algorithm tradeoffs is crucial for choosing right solution.'
    },
    {
        'question': 'What is the time complexity of Quick Sort in best, average, and worst cases? When does worst case occur?',
        'short_description': 'Quick Sort complexity analysis',
        'category': dsa_cat,
        'topic': topics_map['Sorting & Searching'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Quick Sort', 'Time Complexity', 'Analysis'],
        'hints': ['Best/Average: O(n log n)', 'Worst: O(n²)', 'Worst when already sorted and bad pivot choice'],
        'expected_answer': 'Best case: O(n log n) when pivot divides array evenly. Average case: O(n log n) with random pivot. Worst case: O(n²) when pivot is always smallest/largest (already sorted array with first/last as pivot). Space: O(log n) for recursion. Randomized pivot selection avoids worst case.',
        'explanation': 'Shows understanding of algorithm behavior under different input conditions.'
    },
    
    # Hashing - Easy/Medium
    {
        'question': 'What is a Hash Table? Explain collision resolution techniques.',
        'short_description': 'Hash table and collision resolution',
        'category': dsa_cat,
        'topic': topics_map['Hashing'],
        'difficulty': 'Medium',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Hashing', 'Hash Table', 'Collision', 'Data Structures'],
        'hints': ['Hash function maps keys to indices', 'Collisions when two keys hash to same index', 'Chaining vs Open Addressing'],
        'expected_answer': 'Hash Table: Data structure using hash function to map keys to array indices for O(1) average access. Collision Resolution: 1. Chaining - store colliding elements in linked list at same index. 2. Open Addressing - find next empty slot (Linear Probing, Quadratic Probing, Double Hashing).',
        'explanation': 'Critical data structure for interview problems involving fast lookups.'
    },
    {
        'question': 'How do you find the first non-repeating character in a string using hashing?',
        'short_description': 'First non-repeating character',
        'category': dsa_cat,
        'topic': topics_map['Hashing'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Hashing', 'Strings', 'Frequency Count'],
        'hints': ['Use hash map to store character frequencies', 'First pass: count frequencies', 'Second pass: find first with count 1'],
        'expected_answer': 'Create a hash map (or array of size 256 for ASCII). First pass: increment count for each character. Second pass: iterate string again, return first character with count==1. If none found, return null. Time: O(n), Space: O(1) for fixed character set.',
        'explanation': 'Common string manipulation problem using hashing for efficient frequency counting.'
    },
    
    # Recursion - Easy/Medium
    {
        'question': 'What is recursion? Explain with the example of calculating factorial. What is the base case?',
        'short_description': 'Recursion and factorial',
        'category': dsa_cat,
        'topic': topics_map['Recursion'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Recursion', 'Factorial', 'Base Case'],
        'hints': ['Function calling itself', 'Must have base case to stop', 'Factorial: n! = n * (n-1)!'],
        'expected_answer': 'Recursion: Function calling itself to solve smaller subproblems. Factorial: factorial(n) { if (n <= 1) return 1; // base case return n * factorial(n-1); // recursive case } Base case (n<=1) prevents infinite recursion. Time: O(n), Space: O(n) for call stack.',
        'explanation': 'Fundamental programming concept, used in many algorithms like tree traversal, backtracking.'
    },
    {
        'question': 'What is the difference between recursion and iteration? When should you use each?',
        'short_description': 'Recursion vs Iteration',
        'category': dsa_cat,
        'topic': topics_map['Recursion'],
        'difficulty': 'Easy',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Recursion', 'Iteration', 'Comparison'],
        'hints': ['Recursion uses call stack', 'Iteration uses loops', 'Recursion more intuitive for trees'],
        'expected_answer': 'Recursion: Function calls itself, uses call stack, more memory, cleaner code for tree/graph problems. Iteration: Uses loops, less memory, faster, better for simple repetition. Use recursion for naturally recursive problems (trees, divide-and-conquer). Use iteration for simple loops and when stack overflow is a concern.',
        'explanation': 'Understanding when to use each approach shows problem-solving maturity.'
    },
    
    # Time Complexity - Easy/Medium
    {
        'question': 'What is Big O notation? Explain O(1), O(n), O(log n), and O(n²) with examples.',
        'short_description': 'Big O notation explained',
        'category': dsa_cat,
        'topic': topics_map['Time Complexity'],
        'difficulty': 'Easy',
        'expected_duration': 5,
        'answer_type': 'Text',
        'tags': ['Time Complexity', 'Big O', 'Analysis', 'Fundamentals'],
        'hints': ['Big O describes growth rate', 'Ignore constants and lower terms', 'Focus on worst case'],
        'expected_answer': 'Big O describes algorithm efficiency as input size grows. O(1): Constant - array access, hash lookup. O(log n): Logarithmic - binary search, balanced tree operations. O(n): Linear - single array traversal, linear search. O(n²): Quadratic - nested loops, bubble sort. O(n log n): merge sort, heap sort.',
        'explanation': 'Essential for analyzing algorithm efficiency, asked in almost every technical interview.'
    },
    {
        'question': 'What is the space complexity of a recursive function? How is it different from time complexity?',
        'short_description': 'Space complexity in recursion',
        'category': dsa_cat,
        'topic': topics_map['Time Complexity'],
        'difficulty': 'Medium',
        'expected_duration': 4,
        'answer_type': 'Text',
        'tags': ['Space Complexity', 'Recursion', 'Memory'],
        'hints': ['Space complexity counts memory usage', 'Recursive calls use stack space', 'Each call stores local variables'],
        'expected_answer': 'Space complexity measures memory used by algorithm. Recursive functions use call stack - each call stores parameters, local variables, return address. Stack depth determines space complexity. Example: factorial has O(n) space for n recursive calls. Time complexity measures operations; space complexity measures memory.',
        'explanation': 'Understanding space complexity is important for optimizing memory-constrained systems.'
    }
]

print("=" * 80)
print("SEEDING PART 1: CS FUNDAMENTALS (DSA) - 20 Questions")
print("=" * 80)

created_count = 0
for q_dict in dsa_questions:
    q, created = InterviewQuestion.objects.get_or_create(
        question=q_dict['question'],
        category=q_dict['category'],
        defaults={
            'short_description': q_dict['short_description'],
            'topic': q_dict['topic'],
            'difficulty': q_dict['difficulty'],
            'expected_duration': q_dict['expected_duration'],
            'answer_type': q_dict['answer_type'],
            'tags': q_dict['tags'],
            'hints': q_dict['hints'],
            'expected_answer': q_dict['expected_answer'],
            'explanation': q_dict['explanation'],
            'created_by': admin_user,
            'source': 'Manual'
        }
    )
    if created:
        created_count += 1
        print(f"✓ Created: {q_dict['short_description']}")

print("\n" + "=" * 80)
print(f"Successfully created {created_count} new DSA questions!")
print("=" * 80)

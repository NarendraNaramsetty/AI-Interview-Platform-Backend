import json
import re

def clean_sentence(text):
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    return " ".join(text.split())

# We will compile a base list of categories and questions
categories = [
    # Languages and Web
    ("Python", "What is the difference between PEP 8 and other styling systems in Python?", "PEP 8 is Python's official style guide. It defines standard conventions like using 4 spaces for indentation, variable naming (snake_case), and imports formatting. Adhering to it improves codebase readability.", "pep8, pep 8, python, standard, style, indentation", "coding standard, styling, guide, readability"),
    ("Python", "How does Python handle memory management?", "Python manages memory automatically using a private heap. It relies on a built-in garbage collector that utilizes reference counting and a generational garbage collection algorithm to clean up circular references.", "python, memory, garbage collector, heap, reference counting", "ram, stack, speed, allocation, gc"),
    ("Java", "What is Java JVM architecture?", "The JVM (Java Virtual Machine) consists of: 1. Class Loader (loads, links, initializes classes). 2. Runtime Data Areas (Method Area, Heap, Stack, PC Register, Native Method Stack). 3. Execution Engine (Interpreter, JIT Compiler, Garbage Collector).", "java, jvm, memory, bytecode, execution", "interpreter, compiler, engine, stack, heap"),
    ("Java", "What is Java Spring Boot?", "Spring Boot is an extension of the Spring framework that simplifies configuration through starter dependencies, auto-configuration, and an embedded servlet container (Tomcat), enabling developers to build stand-alone, production-ready apps instantly.", "java, spring, spring boot, backend, framework", "enterprise, starter, servlet, tomcat"),
    ("C", "What are pointers in C?", "Pointers are variables that store the memory address of another variable. They are crucial for dynamic memory allocation, array manipulation, and passing arguments by reference to functions.", "c, pointer, address, memory, allocation", "dereference, reference, variables, dynamic"),
    ("C++", "What are virtual functions in C++?", "Virtual functions are member functions in a base class that you expect to redefine in derived classes. They enable dynamic dispatch / runtime polymorphism using virtual table (vtable) pointers.", "cpp, virtual, polymorphism, base, inheritance, derived", "overriding, dynamic, runtime, class"),
    ("JavaScript", "Explain closures in JavaScript.", "A closure is a function that remembers and accesses variables from its outer lexical scope, even when that function is executed outside its original scope. They are used for data privacy and state preservation.", "javascript, js, closure, scope, lexical, variables", "nested function, private, encapsulation, environment"),
    ("JavaScript", "What is the event loop in JavaScript?", "The Event Loop is a mechanism that allows JavaScript to perform non-blocking, asynchronous operations despite being single-threaded. It monitors the Call Stack and the Callback Queue, pushing callback tasks onto the stack when it is empty.", "javascript, js, event loop, async, single-threaded, stack, queue", "asynchronous, callbacks, promise, concurrency"),
    ("TypeScript", "What are interfaces vs types in TypeScript?", "Both define shapes of objects. Interfaces can be extended using 'extends' and support declaration merging (defining same interface multiple times aggregates fields). Types are more versatile (support unions, intersections, primitives) but cannot be merged.", "typescript, ts, interface, type, alias, merge", "shape, object type, union, intersection"),
    ("HTML", "What is semantic HTML?", "Semantic HTML uses tags that clearly describe their meaning to both the browser and the developer (e.g. <header>, <article>, <section>, <footer>) instead of generic tags like <div> or <span>, improving accessibility and SEO.", "html, semantic, tags, seo, structure, access", "seo, markup, layout, element, hierarchy"),
    ("CSS", "What is the CSS Box Model?", "The CSS Box Model is the foundation of design layouts. It treats every element as a rectangular box consisting of: 1. Content (text/images). 2. Padding (space inside border). 3. Border (around padding). 4. Margin (space outside border).", "css, box model, padding, margin, border, layout", "sizing, border box, margin box, style"),
    ("Bootstrap", "How does the Bootstrap grid system work?", "Bootstrap uses a 12-column responsive grid system built on Flexbox. It uses containers, rows, and columns to align content, adjusting dynamically based on screen sizes (xs, sm, md, lg, xl, xxl).", "bootstrap, grid, column, row, flexbox, responsive", "layout, frontend framework, responsive design"),
    ("Tailwind", "What are the advantages of Tailwind CSS?", "Tailwind CSS is a utility-first CSS framework. It provides low-level utility classes directly inside HTML, eliminating the need to write custom CSS files, ensuring consistent designs, and reducing production bundle sizes via purging.", "tailwind, css, utility, class, style, responsive", "inline styling, frontend design, css utility"),
    ("Redux", "What is Redux state management?", "Redux is a predictable state container for JS apps. It stores the entire app state in a single immutable store. State changes are made by dispatching actions to pure functions called reducers, which compute the next state.", "redux, state, store, action, reducer, dispatch", "flux, hooks, global state, context api"),
    ("Next.js", "What is Server-Side Rendering (SSR) in Next.js?", "SSR renders HTML pages on the server for each request. It improves SEO and initial page load speed compared to Client-Side Rendering, and is implemented in Next.js using `getServerSideProps` or Server Components.", "next, nextjs, ssr, rendering, server, seo", "server components, framework, hydration"),
    ("Node.js", "What is Node.js and its architecture?", "Node.js is an open-source, cross-platform JavaScript runtime environment built on Chrome's V8 engine. It uses an event-driven, non-blocking I/O model (backed by the libuv library) to build scalable network applications.", "node, nodejs, v8, async, libuv, runtime", "javascript backend, event driven, server side js"),
    ("Express", "What is middleware in Express.js?", "Middleware functions are functions that have access to the request object (req), response object (res), and the next middleware function in the application's request-response cycle. They perform validation, logging, or auth checks.", "express, middleware, route, handler, cycle", "interceptor, filter, requests, routing"),
    ("Flask", "What is Flask in Python?", "Flask is a micro web framework in Python. It is lightweight, unopinionated, and easy to scale up for APIs, providing core routing and request handling while letting developers choose their own database layers.", "flask, python, microframework, api, backend", "wsgi, light backend, simple api"),
    ("FastAPI", "Why choose FastAPI over Django?", "FastAPI is chosen for high-performance API endpoints. It is built on ASGI, natively supports asynchronous programming, uses Pydantic for data validation, and automatically generates interactive Swagger/OpenAPI docs.", "fastapi, python, asgi, async, pydantic, swagger, openapi", "speed, validation, api documentation"),
    
    # Databases
    ("MySQL", "What are primary keys vs foreign keys in MySQL?", "A primary key uniquely identifies each record in a database table and cannot contain NULL values. A foreign key is a column that establishes a link/relationship between two tables, referencing a primary key in another table.", "mysql, sql, primary key, foreign key, constraint, relationship", "database link, unique id, referential integrity"),
    ("PostgreSQL", "What are PostgreSQL indexes?", "PostgreSQL indexes speed up query lookups by creating a separate data structure (like B-Tree, Hash, GIN) mapping keys to table rows. They speed up SELECT queries but add overhead to INSERT/UPDATE operations.", "postgresql, postgres, index, btree, query, speed", "database optimization, lookup, search speed"),
    ("MongoDB", "What is MongoDB database?", "MongoDB is a NoSQL, document-oriented database. It stores data in flexible, JSON-like BSON documents instead of rows and columns, making it ideal for unstructured data and rapid schema iterations.", "mongodb, mongo, nosql, document, bson, collection", "non relational, schema-less, document database"),
    ("Redis", "How does Redis work as a cache?", "Redis is an in-memory, key-value data store. It keeps all data in RAM, offering sub-millisecond read/write speeds, making it ideal for caching session data, user profiles, or high-frequency API responses.", "redis, cache, memory, key-value, speed, nosql", "in-memory database, pubsub, session store"),
    ("DBMS", "What are ACID properties in database management?", "ACID properties ensure reliable database transactions: 1. Atomicity (all changes succeed or none). 2. Consistency (DB states remain valid). 3. Isolation (concurrent transactions do not interfere). 4. Durability (committed changes persist after failures).", "dbms, database, acid, transaction, consistency, isolation", "integrity, commit, rollback, reliability"),
    
    # CS Subjects & Software
    ("Operating System", "What is a deadlock and its conditions?", "A deadlock occurs when processes are unable to proceed because each is waiting for a resource held by another. Conditions: 1. Mutual Exclusion. 2. Hold and Wait. 3. No Preemption. 4. Circular Wait.", "deadlock, os, conditions, mutual exclusion, resource, processes", "operating system, wait, blocking, threads"),
    ("Operating System", "Explain virtual memory.", "Virtual memory is a storage allocation scheme that mapping peripheral storage to primary storage. It allows the execution of processes that may not be completely in main memory, using paging and page replacement policies.", "virtual memory, paging, ram, disk, swap, cache", "memory allocation, paging table, segment"),
    ("Computer Networks", "What is TCP vs UDP?", "TCP (Transmission Control Protocol) is connection-oriented, reliable, guarantees packet delivery and ordering, and has flow control. UDP (User Datagram Protocol) is connectionless, speed-focused, unreliable, and has no flow/error control (used in video streaming/gaming).", "tcp, udp, protocol, packets, connection, reliability", "osi model, transport layer, connectionless, streaming"),
    ("Computer Networks", "Explain HTTP status codes.", "HTTP status codes indicate response categories: 1xx (Informational), 2xx (Success, e.g. 200 OK, 201 Created), 3xx (Redirection, e.g. 301, 302), 4xx (Client Error, e.g. 400 Bad Request, 401 Unauthorized, 404 Not Found), 5xx (Server Error, e.g. 500 Internal Error).", "http, status code, 404, 200, 500, error, success", "network protocols, web responses, status messages"),
    ("Data Structures", "What is a Binary Search Tree (BST)?", "A BST is a node-based binary tree data structure where: 1. The left subtree of a node contains only nodes with keys less than the parent. 2. The right subtree contains only nodes with keys greater than the parent. 3. Both subtrees must also be BSTs. Search/Insert takes O(log N) average time.", "dsa, bst, tree, binary search tree, search, node", "data structures, sorting, nodes, graph"),
    ("Algorithms", "What is quicksort algorithm complexity?", "Quicksort is a divide-and-conquer algorithm. It selects a pivot, partitions the array around the pivot, and recursively sorts sub-arrays. Average time complexity is O(N log N). Worst-case is O(N^2) if pivot choices are poor (e.g. sorted array), and space complexity is O(log N) auxiliary.", "quicksort, quick, complexity, worst case, pivot, partition", "sorting algorithms, speed, complexity analysis"),
    ("System Design", "What is the difference between Horizontal and Vertical scaling?", "Vertical scaling (scaling up) means adding more power (CPU, RAM) to your existing server database. It has a hardware ceiling. Horizontal scaling (scaling out) means adding more machines/servers to your pool and distributing load via a Load Balancer, offering high availability.", "scaling, horizontal, vertical, system design, load balancer, hardware", "scale out, scale up, servers, high availability, database scaling")
]

generated_list = []
seen_questions = set()
id_counter = 1

# 1. Add static base list
for cat, question, answer, keywords, synonyms in categories:
    clean_q = clean_sentence(question)
    if clean_q not in seen_questions:
        entry = {
            "title": f"{cat} Interview Prep Q{id_counter}",
            "category": cat,
            "question": question,
            "answer": answer,
            "keywords": keywords,
            "synonyms": synonyms,
            "priority": 5,
            "difficulty": "Medium",
            "tags": f"{cat.lower()}, prep, interview",
            "is_active": True
        }
        generated_list.append(entry)
        seen_questions.add(clean_q)
        id_counter += 1

# 2. Programmatically generate 100+ entries for Companies
companies = [
    "TCS", "Infosys", "Wipro", "Accenture", "Capgemini", "HCL", "Tech Mahindra", 
    "LTIMindtree", "Cognizant", "Amazon", "Google", "Microsoft", "Oracle", 
    "Adobe", "IBM", "Deloitte", "EY", "PwC"
]

for company in companies:
    # Q1: General Process
    q1 = f"What is the recruitment and interview process for {company}?"
    ans1 = f"The recruitment process at {company} generally includes an online aptitude and technical assessment test, followed by 1 or 2 technical interview rounds focusing on core subjects (OOP, DBMS, OS, coding/DSA) and projects, concluding with a managerial/HR round."
    kw1 = f"{company.lower()}, process, round, recruitment, hiring"
    syn1 = "test, placement, interview, campus"
    
    # Q2: Coding test preparation
    q2 = f"How do I prepare for the coding rounds at {company}?"
    ans2 = f"To crack {company} coding rounds: 1. Practice basic and intermediate coding problems (arrays, strings, searching, sorting). 2. Understand time and space complexity. 3. Be ready to explain your logic and dry-run with sample test cases. For product companies like Amazon/Google, focus heavily on tree, graph, and dynamic programming algorithms."
    kw2 = f"{company.lower()}, coding round, prepare, coding test, dsa"
    syn2 = "programming, test prep, problems, practice"
    
    # Q3: Behavioral fit
    q3 = f"What behavioral traits is {company} looking for in candidates?"
    ans3 = f"In interviews, {company} evaluates core behavioral qualities like teamwork, problem-solving under pressure, adaptability to new technologies/locations, clear communication, and leadership capabilities. Use the STAR method to describe project achievements."
    kw3 = f"{company.lower()}, behavioral, traits, cultural, value"
    syn3 = "hr, situational, fit, soft skills"

    for q, ans, kw, syn in [(q1, ans1, kw1, syn1), (q2, ans2, kw2, syn2), (q3, ans3, kw3, syn3)]:
        clean_q = clean_sentence(q)
        if clean_q not in seen_questions:
            entry = {
                "title": f"{company} Placement Prep Q{id_counter}",
                "category": company,
                "question": q,
                "answer": ans,
                "keywords": kw,
                "synonyms": syn,
                "priority": 4,
                "difficulty": "Medium",
                "tags": f"{company.lower()}, placements, company prep",
                "is_active": True
            }
            generated_list.append(entry)
            seen_questions.add(clean_q)
            id_counter += 1

# 3. Programmatically generate 50+ entries for Roadmaps
roadmaps = [
    ("AI Roadmap", "Artificial Intelligence", ["Python", "Machine Learning", "Deep Learning", "NLP", "Embeddings"]),
    ("Data Analyst Roadmap", "Data Analyst", ["SQL", "Excel", "Tableau", "PowerBI", "Pandas"]),
    ("Software Engineer Roadmap", "Software Engineer", ["DSA", "System Design", "Databases", "Git", "OOP"]),
    ("Full Stack Roadmap", "Full Stack Developer", ["HTML/CSS", "JavaScript", "React", "Node.js", "PostgreSQL"]),
    ("Backend Roadmap", "Backend Engineer", ["Django", "FastAPI", "Express", "Caching", "Docker"]),
    ("Frontend Roadmap", "Frontend Developer", ["React", "CSS", "Next.js", "Redux", "Tailwind"]),
    ("Machine Learning Roadmap", "Machine Learning Engineer", ["Scikit-Learn", "PyTorch", "TensorFlow", "Math", "MLOps"]),
    ("Data Science Roadmap", "Data Scientist", ["Statistics", "Python", "SQL", "Big Data", "EDA"])
]

for roadmap_name, role, skills in roadmaps:
    # Q1: General roadmap path
    q1 = f"What is the complete roadmap to become a {role}?"
    ans1 = f"To become a {role}, follow this step-by-step roadmap: 1. Master the fundamentals (languages and math). 2. Learn core technologies: {', '.join(skills[:3])}. 3. Work on hands-on projects integrating these concepts. 4. Master version control (Git) and deployment basics. 5. Practice interview questions and coding mock assessments."
    kw1 = f"{roadmap_name.lower().replace(' ', ', ')}, roadmap, learning, path, guide"
    syn1 = "steps, timeline, courses, transition"

    # Q2: Key skills
    q2 = f"What are the core skills required for a {role}?"
    ans2 = f"The essential technical skills for a {role} include: {', '.join(skills)}. In addition to these tech stacks, you must develop strong problem-solving skills, debugging expertise, and effective communication skills."
    kw2 = f"{roadmap_name.lower().replace(' ', ', ')}, skills, requirements, stack"
    syn2 = "must know, tools, languages"

    for q, ans, kw, syn in [(q1, ans1, kw1, syn1), (q2, ans2, kw2, syn2)]:
        clean_q = clean_sentence(q)
        if clean_q not in seen_questions:
            entry = {
                "title": f"{roadmap_name} Prep Q{id_counter}",
                "category": roadmap_name,
                "question": q,
                "answer": ans,
                "keywords": kw,
                "synonyms": syn,
                "priority": 4,
                "difficulty": "Easy",
                "tags": f"{roadmap_name.lower().replace(' ', '-')}, roadmap, guide",
                "is_active": True
            }
            generated_list.append(entry)
            seen_questions.add(clean_q)
            id_counter += 1

# 4. Add government exams, reasoning & aptitude questions (SSC, Bank)
ssc_exams = ["SSC CGL", "SSC CHSL", "Bank PO", "Bank Clerk"]
for exam in ssc_exams:
    q1 = f"What is the exam pattern and selection process for {exam}?"
    ans1 = f"The selection process for {exam} typically consists of multiple Tiers or Phases. The preliminary stage tests Quantitative Aptitude, Logical Reasoning, English Comprehension, and General Awareness. Subsequent stages assess specialized/descriptive subjects, computer typing, or interviews (for PO roles)."
    kw1 = f"{exam.lower().replace(' ', ', ')}, pattern, exam, selection, syllabus"
    syn1 = "ssc, bank, recruitment, marks, tier"
    
    q2 = f"How should I prepare for the quantitative aptitude section of {exam}?"
    ans2 = f"To excel in the QA section: 1. Build speed by practicing mental math and short tricks. 2. Focus on high-weightage topics like Ratio/Proportion, Percentages, Profit & Loss, Interest, and Time & Work. 3. Attempt daily mock tests and review mistakes."
    kw2 = f"{exam.lower().replace(' ', ', ')}, quantitative, math, aptitude, speed"
    syn2 = "quant, calculations, mock test, tricks"

    for q, ans, kw, syn in [(q1, ans1, kw1, syn1), (q2, ans2, kw2, syn2)]:
        clean_q = clean_sentence(q)
        if clean_q not in seen_questions:
            entry = {
                "title": f"{exam} Exam Prep Q{id_counter}",
                "category": exam,
                "question": q,
                "answer": ans,
                "keywords": kw,
                "synonyms": syn,
                "priority": 3,
                "difficulty": "Medium",
                "tags": f"{exam.lower().replace(' ', '-')}, government exams",
                "is_active": True
            }
            generated_list.append(entry)
            seen_questions.add(clean_q)
            id_counter += 1

# Write the final large list to file
with open("d:\\interview\\backend\\chatbot\\data\\knowledge_entries.json", "w") as f:
    json.dump(generated_list, f, indent=2)

print(f"Successfully generated {len(generated_list)} entries in knowledge_entries.json!")

#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <chrono>
#include <ncurses.h>
#include <unistd.h>
#include <atomic>
#include <csignal>
#include <deque>

enum State { THINKING, HUNGRY, EATING };

class DiningPhilosophers {
private:
    int n;
    std::vector<State> state;
    std::vector<int> eat_count;
    std::vector<int> think_count;
    std::vector<int> fork_owner; // -1 free, otherwise philosopher id holding both adjacent forks
    std::vector<bool> in_queue;
    std::deque<int> wait_queue; // FIFO to avoid starvation
    std::vector<std::condition_variable> cv;
    std::mutex mtx; // monitor lock guarding state/cv
    std::mutex display_mutex;
    std::atomic<bool> running;

    static DiningPhilosophers* instance;
    static void handle_sigint(int) {
        if (instance) instance->stop();
    }

    void test_front() {
        // Requires mtx to be held; serves requests in FIFO to prevent starvation
        if (wait_queue.empty()) return;
        int i = wait_queue.front();
        if (state[i] == HUNGRY && state[(i - 1 + n) % n] != EATING && state[(i + 1) % n] != EATING) {
            wait_queue.pop_front();
            in_queue[i] = false;
            state[i] = EATING;
            ++eat_count[i];
            fork_owner[i] = i;
            fork_owner[(i + 1) % n] = i;
            cv[i].notify_one();
        }
    }

    void pickup(int i) {
        std::unique_lock<std::mutex> lock(mtx);
        if (!in_queue[i]) {
            wait_queue.push_back(i);
            in_queue[i] = true;
        }
        state[i] = HUNGRY;
        test_front();
        cv[i].wait(lock, [&]{ return state[i] == EATING || !running.load(); });
    }

    void putdown(int i) {
        std::lock_guard<std::mutex> lock(mtx);
        state[i] = THINKING;
        ++think_count[i];
        fork_owner[i] = -1;
        fork_owner[(i + 1) % n] = -1;
        test_front();
    }

    void philosopher(int id) {
        while (running) {
            // Thinking
            std::this_thread::sleep_for(std::chrono::milliseconds(rand() % 2000 + 1000));
            
            // Eating
            pickup(id);
            if (!running.load()) break; // exit early if stop was requested while waiting
            std::this_thread::sleep_for(std::chrono::milliseconds(rand() % 1000 + 500));
            putdown(id);
        }
    }

    void display_loop() {
        nodelay(stdscr, TRUE); // allow non-blocking key check
        while (running) {
            {
                std::lock_guard<std::mutex> lock(display_mutex);
                std::lock_guard<std::mutex> state_lock(mtx);
                clear();
                mvprintw(0, 0, "=== Dining Philosophers (%d) ===", n);
                mvprintw(2, 0, "Philosophers:");
                mvprintw(3, 0, "Idx  State       Ate  Thought");
                
                for (int i = 0; i < n; i++) {
                    const char* state_str = (state[i] == THINKING) ? "THINKING" : 
                                           (state[i] == HUNGRY) ? "HUNGRY" : "EATING";
                    mvprintw(4 + i, 0, "  %2d  %-10s  %4d  %7d", i, state_str, eat_count[i], think_count[i]);
                }

                mvprintw(5 + n, 0, "Waiting queue (front -> back):");
                int line = 6 + n;
                if (wait_queue.empty()) {
                    mvprintw(line, 0, "  empty");
                } else {
                    int col = 0;
                    for (int id : wait_queue) {
                        mvprintw(line, col, "%d ", id);
                        col += 3;
                    }
                }

                mvprintw(7 + n, 0, "Forks (between i and i+1):");
                for (int i = 0; i < n; i++) {
                    int owner = fork_owner[i];
                    if (owner == -1) {
                        mvprintw(8 + n + i, 0, "  Fork %2d-%-2d: free", i, (i + 1) % n);
                    } else {
                        mvprintw(8 + n + i, 0, "  Fork %2d-%-2d: held by %d", i, (i + 1) % n, owner);
                    }
                }
                
                mvprintw(9 + 2 * n + 2, 0, "Press Ctrl+C or 'q' to exit");
                refresh();
            }
            int ch = getch();
            if (ch == 'q' || ch == 'Q') {
                stop();
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(400));
        }
    }

public:
    DiningPhilosophers(int num) : n(num), state(num, THINKING), eat_count(num, 0), think_count(num, 0), fork_owner(num, -1), in_queue(num, false), cv(num), running(true) {
        instance = this;
        signal(SIGINT, handle_sigint);
        initscr();
        noecho();
        cbreak();
    }

    ~DiningPhilosophers() {
        endwin();
    }

    void run() {
        std::vector<std::thread> threads;
        
        std::thread display(&DiningPhilosophers::display_loop, this);
        
        for (int i = 0; i < n; i++) {
            threads.emplace_back(&DiningPhilosophers::philosopher, this, i);
        }
        
        for (auto& t : threads) {
            t.join();
        }

        display.join();
    }

    void stop() {
        running = false;
        std::lock_guard<std::mutex> lock(mtx);
        for (auto& c : cv) {
            c.notify_all();
        }
    }
};

DiningPhilosophers* DiningPhilosophers::instance = nullptr;

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <number_of_philosophers>\n";
        std::cerr << "Number of philosophers must be >= 5\n";
        return 1;
    }

    int n = std::stoi(argv[1]);
    if (n < 5) {
        std::cerr << "Number of philosophers must be at least 5\n";
        return 1;
    }

    DiningPhilosophers dp(n);
    dp.run();

    return 0;
}
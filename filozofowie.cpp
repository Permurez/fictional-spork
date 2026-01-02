#include <iostream>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>
#include <chrono>
#include <ncurses.h>
#include <unistd.h>

enum State { THINKING, HUNGRY, EATING };

class DiningPhilosophers {
private:
    int n;
    std::vector<State> state;
    std::vector<std::mutex> forks;
    std::vector<std::condition_variable> cv;
    std::mutex display_mutex;
    bool running;

    void test(int i) {
        if (state[i] == HUNGRY && state[(i - 1 + n) % n] != EATING && state[(i + 1) % n] != EATING) {
            state[i] = EATING;
            cv[i].notify_one();
        }
    }

    void pickup(int i) {
        std::unique_lock<std::mutex> lock(forks[i]);
        state[i] = HUNGRY;
        test(i);
        while (state[i] != EATING) {
            cv[i].wait(lock);
        }
    }

    void putdown(int i) {
        std::unique_lock<std::mutex> lock(forks[i]);
        state[i] = THINKING;
        test((i - 1 + n) % n);
        test((i + 1) % n);
    }

    void philosopher(int id) {
        while (running) {
            // Thinking
            std::this_thread::sleep_for(std::chrono::milliseconds(rand() % 2000 + 1000));
            
            // Eating
            pickup(id);
            std::this_thread::sleep_for(std::chrono::milliseconds(rand() % 1000 + 500));
            putdown(id);
        }
    }

    void display_loop() {
        while (running) {
            {
                std::lock_guard<std::mutex> lock(display_mutex);
                clear();
                mvprintw(0, 0, "=== Dining Philosophers (%d) ===", n);
                mvprintw(2, 0, "Philosophers:");
                
                for (int i = 0; i < n; i++) {
                    const char* state_str = (state[i] == THINKING) ? "THINKING" : 
                                           (state[i] == HUNGRY) ? "HUNGRY" : "EATING";
                    mvprintw(3 + i, 0, "  Philosopher %d: %s", i, state_str);
                }
                
                mvprintw(3 + n + 2, 0, "Press Ctrl+C to exit");
                refresh();
            }
            std::this_thread::sleep_for(std::chrono::milliseconds(400));
        }
    }

public:
    DiningPhilosophers(int num) : n(num), state(num, THINKING), forks(num), running(true) {
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
        
        running = false;
        display.join();
    }

    void stop() {
        running = false;
    }
};

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
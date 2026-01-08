#ifndef UPDATE_EVENT_H
#define UPDATE_EVENT_H

#include <functional>
#include <vector>
#include <cstddef>

// Simple update event that widgets can subscribe to.
// Subscribers are callables with signature void().
class UpdateEvent {
public:
    using Callback = std::function<void()>;

    // Subscribe a callback. Returns a subscription id for possible unsubscribe.
    std::size_t Subscribe(Callback cb) {
        std::size_t id = next_id_++;
        callbacks_.emplace_back(id, std::move(cb));
        return id;
    }

    // Unsubscribe by id. No-op if id not found.
    void Unsubscribe(std::size_t id) {
        for (auto it = callbacks_.begin(); it != callbacks_.end(); ++it) {
            if (it->first == id) { callbacks_.erase(it); return; }
        }
    }

    // Notify all subscribers.
    void Notify() {
        // iterate over a copy in case subscribers modify subscriptions
        auto copy = callbacks_;
        for (auto &p : copy) {
            if (p.second) p.second();
        }
    }

private:
    std::vector<std::pair<std::size_t, Callback>> callbacks_;
    std::size_t next_id_ = 1;
};

#endif // UPDATE_EVENT_H

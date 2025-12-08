// Minimal stub of yaml-cpp for dev builds when yaml-cpp is not available.
#pragma once
#include <string>
namespace YAML {
  class Node {
  public:
    Node() = default;
    Node operator[](const std::string&) const { return Node(); }
    template<typename T>
    T as() const { return T(); }
    operator bool() const { return false; }
  };

  inline Node LoadFile(const std::string&) { return Node(); }
}

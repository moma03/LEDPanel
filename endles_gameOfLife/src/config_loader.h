#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H

#include <string>
#include "led-matrix.h"

// Loads matrix and runtime options from a JSON config file.
// Returns true on success, false on failure.
bool LoadMatrixOptionsFromConfig(const std::string& path,
                                 rgb_matrix::RGBMatrix::Options& matrix_options,
                                 rgb_matrix::RuntimeOptions& runtime_opt);

#endif // CONFIG_LOADER_H

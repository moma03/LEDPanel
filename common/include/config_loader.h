#ifndef CONFIG_LOADER_H
#define CONFIG_LOADER_H

#include <string>
#include <led-matrix.h>


// Loads matrix and cube renderer options from a JSON config file
bool LoadConfigFromFile(const std::string& path,
                       rgb_matrix::RGBMatrix::Options& matrix_options,
                       rgb_matrix::RuntimeOptions& runtime_opt);

// Calculate actual display dimensions accounting for chain_length, parallel, and pixel mapper
void GetDisplayDimensions(const rgb_matrix::RGBMatrix::Options& matrix_options,
                         int& out_width, int& out_height);


#endif // CONFIG_LOADER_H

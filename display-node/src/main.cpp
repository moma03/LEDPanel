// Fetch Next 10 Stops from postgres DB and display them on the LED matrix

#include <unistd.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>
#include <vector>
#include <cstdlib>
#include <iostream>
#include <math.h>

#include "config_loader.h"
#include "led-matrix.h"

using namespace rgb_matrix;
using std::min;
using std::max;

bool isDebug = true; // Set to true to enable debug output


class BahnhofDisplay {public:
    BahnhofDisplay(Canvas *canvas) : canvas_(canvas) {}

    void ShowStation(const std::string &station_name) {
        // Clear the canvas
        canvas_->Clear();

        if (isDebug) {
            std::cout << "Displaying station: " << station_name << std::endl;
            
        }
    }

    // Get Station Stops from Database
    std::vector<std::string> GetNextStops(const std::string &station_name) {
        

private:
    Canvas *const canvas_;
};

class Stop {
public:
    Stop(const std::string &name, const std::string &eva_number)
        : name_(name), eva_number_(eva_number) {}

    std::string GetName() const { return name_; }
    std::string GetEVANumber() const { return eva_number_; }

private:
    std::string name_;
    std::string eva_number_;
};

static int usage(const char *progname) {
    fprintf(stderr, "Usage: %s [options] -StationName <station_name> -StationEVA <eva_number>\n", progname);
    fprintf(stderr, "Options:\n");
    fprintf(stderr, "\t-StationName <station_name>   : Name of the station to display\n");
    fprintf(stderr, "\t-StationEVA <eva_number>      : EVA number of the station\n");
    rgb_matrix::PrintMatrixFlags(stderr);
    return 1;
}

int main(int argc, char *argv[]) {
    std::string station_name;
    std::string station_eva;

    RGBMatrix::Options matrix_options;
    rgb_matrix::RuntimeOptions runtime_opt;

    // Load options from config file
    if (!LoadMatrixOptionsFromConfig("config.json", matrix_options, runtime_opt)) {
        std::cerr << "Error: Could not open or parse config.json file." << std::endl;
        return 1;
    }

    

    // Parse command line options
    int opt;
    while ((opt = getopt(argc, argv, "StationName:StationEVA:")) != -1) {
        switch (opt) {
            case 'S':
                station_name = optarg;
                break;
            case 'E':
                station_eva = optarg;
                break;
            default:
                return usage(argv[0]);
        }
    }

    if (station_name.empty() && station_eva.empty()) {
        fprintf(stderr, "Error: Both -StationName or -StationEVA must be provided.\n");
        return usage(argv[0]);
    }

    RGBMatrix *matrix = RGBMatrix::CreateFromOptions(matrix_options, runtime_opt);
    if (matrix == NULL)
        return 1;

    Canvas *canvas = matrix;

    BahnhofDisplay display(canvas);
    display.ShowStation(station_name);

    // Keep the display for a while
    sleep(10);

    delete matrix;
    return 0;
}
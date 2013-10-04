#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"
#include <iostream>
#include <fstream>
#include <stdio.h>
#include <dirent.h>
#include <sys/time.h>
#include <unistd.h>

using namespace std;
using namespace cv;

typedef unsigned long long timestamp_t;

const string CONFIGFILE = "readScore.config";

/// Control flags
bool showAOI = false;
bool showSpeed = false;
bool debug = false;

/// Function Headers
timestamp_t get_timestamp ();
map<string,string> readConfig();
string matchScore(string color, Mat img);

/** @function main */
int main( int argc, char** argv )
{
	map<string,string> configs = readConfig();

	if (configs["visualMode"] == "true") {
		showAOI = true;
	}
	if (configs["showSpeed"] == "true") {
		showSpeed = true;
	}
	if (configs["debug"] == "true") {
		debug = true;
	}

	VideoCapture vcap;
	Mat src;

	const string videoStreamAddress = configs["streamAddress"];

	//open the video stream and make sure it's opened
	if(!vcap.open(videoStreamAddress)) {
		cout << "Error opening video stream or file" << endl;
		return -1;
	}

	/// Set areas of interest (AOI)
	Rect blueArea = Rect(atoi(configs["blueX"].c_str()), atoi(configs["blueY"].c_str()),
			atoi(configs["blueW"].c_str()), atoi(configs["blueH"].c_str()));
	Rect redArea = Rect(atoi(configs["redX"].c_str()), atoi(configs["redY"].c_str()),
			atoi(configs["redW"].c_str()), atoi(configs["redH"].c_str()));

	stringstream jsonStringOld;
	ofstream jsonFile;

	for(;;) {
		timestamp_t t0, t1;
		t0 = t1 = 0;
		while (t1-t0 < 100000) {
			t0 = get_timestamp();
			vcap.grab();
			t1 = get_timestamp();
		}

		timestamp_t t_start = 0;
		if (showSpeed) t_start = get_timestamp();

		if(!vcap.read(src)) {
			std::cout << "error: vcap.read(src)\n";
			vcap.release();
			usleep(5000000);
			vcap.open(videoStreamAddress);
			continue;
		}

		/// Should we display AOI or calculate score?
		if (showAOI) {
			Mat imgBlueRect;
			src.copyTo(imgBlueRect);
			rectangle(imgBlueRect, blueArea, Scalar( 255, 0, 0 ), 2);
			namedWindow( "Blue Area", CV_WINDOW_AUTOSIZE );
			imshow( "Blue Area", imgBlueRect );

			Mat imgRedRect;
			src.copyTo(imgRedRect);
			rectangle(imgRedRect, redArea, Scalar( 0, 0, 255 ), 2);
			namedWindow( "Red Area", CV_WINDOW_AUTOSIZE );
			imshow( "Red Area", imgRedRect );

			waitKey(0);
		} else {
			try {
				Mat imgBlue =  Mat(src, blueArea);
				Mat imgRed =  Mat(src, redArea);

				// calculate score
				string blueScore = matchScore("blue", imgBlue);
				string redScore = matchScore("red", imgRed);

				if (!blueScore.empty() && !redScore.empty()) {
					stringstream jsonStringNew;
					jsonStringNew << "{\"score\":{\"blue\": \""
							<< blueScore
							<< "\",\"red\": \""
							<< redScore
							<< "\"}}\n";

					if (jsonStringNew.str() != jsonStringOld.str()) {

						string cmd = "curl -X POST -H \"Content-Type: application/json\" "
								"-d '" + jsonStringNew.str() + "' "
								+ configs["jsonEndpoint"] + ">/dev/null &";
						if (system(cmd.c_str())){}

						jsonFile.open ("/tmp/score.json");
						jsonFile << jsonStringNew.str();
						jsonFile.close();

						jsonStringOld.clear();
						jsonStringOld << jsonStringNew.rdbuf();
					}
				} else {
					std::cout << "error: matchScore returned NULL\n";
				}
			} catch (...) {}

			if (showSpeed) {
				timestamp_t t_end = get_timestamp();
				double secs = (t_end - t_start) / 1000000.0L;
				std::cout << secs << " seconds\n";
			}
		}

		// sleep for 3 second
		usleep(3000000);
	}

	return 0;
}

string matchScore(string color, Mat img)
{
	DIR *dir;
	struct dirent *ent;
	if ((dir = opendir (color.c_str())) != NULL) {
		double min_dist_global = DBL_MAX;
		char* image = NULL;
		while ((ent = readdir (dir)) != NULL) {
			std::string line = string(ent->d_name);
			if (line.find("jpg") != line.npos && line.find("score") == line.npos) {
				string fullPath = color + string("/") + string(ent->d_name);

				Mat templ;
				templ = imread( fullPath, 1 );

				/// Do the Matching and Normalize
				Mat result;
				try {
					matchTemplate( img, templ, result, 0 );
				} catch (...) {
					closedir(dir);
					return String();
				}

				/// Localizing the best match with minMaxLoc
				double minVal; double maxVal; Point minLoc; Point maxLoc;

				minMaxLoc( result, &minVal, &maxVal, &minLoc, &maxLoc, Mat() );

				if (debug) printf("%s minVal: %f \n", fullPath.c_str(), minVal );
				if (minVal < min_dist_global) {
					min_dist_global = minVal;
					image = ent->d_name;
				}
			}
		}
		closedir(dir);
		return String(image).substr(0,2);
	}
	closedir(dir);
	return String();
}

timestamp_t
get_timestamp ()
{
	struct timeval now;
	gettimeofday (&now, NULL);
	return  now.tv_usec + (timestamp_t)now.tv_sec * 1000000;
}

map<string,string> readConfig()
						{
	string line;
	map<string,string>  configs;
	std::ifstream configFile(CONFIGFILE.c_str());
	while(std::getline(configFile, line)) {
		if (!line.empty()) {
			string delimiter = "=";
			string key = line.substr(0, line.find(delimiter));
			line.erase(0, line.find(delimiter) + delimiter.length());
			string value = line.substr(0, line.find(delimiter));
			configs[key] = value;
		}
	}
	configFile.close();

	//	map<string, string>::const_iterator itr;
	//	for(itr = configs.begin(); itr != configs.end(); ++itr){
	//		cout << "Key: " << (*itr).first << " Value: " << (*itr).second << "\n";
	//	}

	return configs;
						}

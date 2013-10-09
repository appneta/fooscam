#include "opencv2/highgui/highgui.hpp"
#include "opencv2/imgproc/imgproc.hpp"

#include <iostream>
#include <fstream>
#include <sys/time.h>
#include <stdio.h>
#include <unistd.h>

using namespace cv;
using namespace std;

typedef unsigned long long timestamp_t;

const string CONFIGFILE = "detectPlayers.config";
map<string,string> configs;

timestamp_t get_timestamp ()
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
	if (!configFile) {
		cout << "Could not find configuration file: " << CONFIGFILE << endl;
	}
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

void resize(Mat& src, int percentage)
{
	int cols = percentage * src.cols / 100;
	int rows = percentage * src.rows / 100;
	resize(src, src, Size(cols,rows));
}

float getSlope(Point pt1, Point pt2)
{
        float fSlope, fYInt, fAngle = 90, fRun = pt2.x - pt1.x;
        bool bInfSlope = (fRun == 0);

        if (!bInfSlope)
        {
                fSlope = (pt2.y - pt1.y)/fRun;
                fAngle = (float)(180.0 * atan((double)fSlope)/M_PI);
                fYInt = -fSlope * pt1.x + pt1.y;
        }
        return fAngle;
}

// Finds the intersection of two lines, or returns false.
// The lines are defined by (o1, p1) and (o2, p2).
bool intersection(Point2f o1, Point2f p1, Point2f o2, Point2f p2,
		Point2f &r)
{
	Point2f x = o2 - o1;
	Point2f d1 = p1 - o1;
	Point2f d2 = p2 - o2;

	float cross = d1.x*d2.y - d1.y*d2.x;
	if (abs(cross) < /*EPS*/1e-8)
		return false;

	double t1 = (x.x * d2.y - x.y * d2.x)/cross;
	r = o1 + d1 * t1;
	return true;
}

void findBorderLines(Mat& dst, vector<Vec2f>& borderLines)
{
	vector<Vec2f> lines;
	HoughLines(dst, lines, 1, CV_PI/180, 50, 0, 0 );

	for( size_t i = 0; i < lines.size(); i++ ) {

		// line 1
		float rho1 = lines[i][0], theta1 = lines[i][1];
		Point aPt1, aPt2;
		double a = cos(theta1), b = sin(theta1);
		double x0 = a*rho1, y0 = b*rho1;
		aPt1.x = cvRound(x0 + 1000*(-b));
		aPt1.y = cvRound(y0 + 1000*(a));
		aPt2.x = cvRound(x0 - 1000*(-b));
		aPt2.y = cvRound(y0 - 1000*(a));

		bool dup = false;

		for( size_t j = 0; j < borderLines.size(); j++ ) {
			if (i != j) {
				// line 2
				float rho2 = borderLines[j][0], theta2 = borderLines[j][1];
				Point bPt1, bPt2;
				double a = cos(theta2), b = sin(theta2);
				double x0 = a*rho2, y0 = b*rho2;
				bPt1.x = cvRound(x0 + 1000*(-b));
				bPt1.y = cvRound(y0 + 1000*(a));
				bPt2.x = cvRound(x0 - 1000*(-b));
				bPt2.y = cvRound(y0 - 1000*(a));

//				cout << "i:" << i << ", j:" << j;
//				cout << ", rho1:" << rho1 << ", rho2:" << rho2 << ", theta1:" << theta1 << ", theta2:" << theta2 << "\n";

				Point2f r;
				r.x = -1; r.y = -1;
				intersection(aPt1, aPt2, bPt1, bPt2, r);
				if ((r.x >= 0) && (r.x <= dst.cols) && (r.y >= 0) && (r.y <= dst.rows)) {
					float slopeDifference = abs(getSlope(aPt1, aPt2) - getSlope(bPt1, bPt2));
					if (slopeDifference < 70 || abs(180 - slopeDifference) < 70) {
						dup = true;
						break;
					}
				}
			}
		}

		if (!dup) {
			borderLines.push_back(lines[i]);
//			cout<<getSlope(aPt1, aPt2)<<endl;
//			cout << "rho1:" << rho1 << ", theta1:" << theta1 << "\n";
		}
	}
//	cout <<endl;
}

void findCorners(Mat& cdst, vector<Vec2f>& borderLines, vector<cv::Point2f>& corners)
{
	for( size_t i = 0; i < borderLines.size(); i++ ) {
		float rho1 = borderLines[i][0], theta1 = borderLines[i][1];
		Point pt1, pt2;
		double a = cos(theta1), b = sin(theta1);
		double x0 = a*rho1, y0 = b*rho1;
		pt1.x = cvRound(x0 + 1000*(-b));
		pt1.y = cvRound(y0 + 1000*(a));
		pt2.x = cvRound(x0 - 1000*(-b));
		pt2.y = cvRound(y0 - 1000*(a));

		line( cdst, pt1, pt2, Scalar(0,0,255), 1, CV_AA);
		for( size_t j = 0; j < borderLines.size(); j++ ) {
			if (i != j) {
				float rho2 = borderLines[j][0], theta2 = borderLines[j][1];
				Point pt3, pt4;
				double a = cos(theta2), b = sin(theta2);
				double x0 = a*rho2, y0 = b*rho2;
				pt3.x = cvRound(x0 + 1000*(-b));
				pt3.y = cvRound(y0 + 1000*(a));
				pt4.x = cvRound(x0 - 1000*(-b));
				pt4.y = cvRound(y0 - 1000*(a));

				// intersection
				Point2f r;
				bool intersect = intersection(pt1, pt2, pt3, pt4, r);
				if (intersect) {
					if ((r.x > 0) && (r.x < cdst.cols) &&
							(r.y > 0) && (r.y < cdst.rows)) {
						bool dup = false;

						// see if we have this intersection already
						for( size_t k = 0; k < corners.size(); k++ ) {
							if ((cvRound(corners[k].x) == cvRound(r.x)) && (cvRound(corners[k].y) == cvRound(r.y))) {
								dup = true;
								break;
							}
						}
						if (!dup) {
							corners.push_back(r);
							circle(cdst, r, 5, Scalar(0,255,0));
						}

					}
				}
			}
		}
	}

}

bool sortCorners(std::vector<cv::Point2f>& corners)
{
    std::vector<cv::Point2f> top, bot;

    if (corners.size() != 4) {
    	return false;
    }

    for (int i = corners.size()-1 ; i > 0 ; i--) {
    	for (int j = 0 ; j < i ; j++) {
    		if (corners[j].y > corners[j+1].y) {  /* compare  */
    			Point2f p = corners[j] ;         /* exchange */
    			corners[j] = corners[j+1];
    			corners[j+1] = p;
    		}
    	}
    }

    cv::Point2f tl = corners[0].x > corners[1].x ? corners[1] : corners[0];
    cv::Point2f tr = corners[0].x > corners[1].x ? corners[0] : corners[1];
    cv::Point2f bl = corners[2].x > corners[3].x ? corners[3] : corners[2];
    cv::Point2f br = corners[2].x > corners[3].x ? corners[2] : corners[3];

    corners.clear();
    corners.push_back(tl);
    corners.push_back(tr);
    corners.push_back(br);
    corners.push_back(bl);

    return true;
}

bool transformPerspective(Mat& src, Mat& quad, vector<cv::Point2f>& corners)
{
	if (!sortCorners(corners)) {
		return false;
	}

//	cout << corners[0].x << "," << corners[0].y << "\n";
//	cout << corners[1].x << "," << corners[1].y << "\n";
//	cout << corners[2].x << "," << corners[2].y << "\n";
//	cout << corners[3].x << "," << corners[3].y << "\n";

	// Corners of the destination image
	std::vector<Point2f> quad_pts;
	quad_pts.push_back(Point2f(0, 0));
	quad_pts.push_back(Point2f(quad.cols, 0));
	quad_pts.push_back(Point2f(quad.cols, quad.rows));
	quad_pts.push_back(Point2f(0, quad.rows));

	try {
		// Get transformation matrix
		Mat transmtx = getPerspectiveTransform(corners, quad_pts);

		// Apply perspective transformation
		warpPerspective(src, quad, transmtx, quad.size());
	} catch (...) {
		return false;
	}

	return true;
}

void rotate(Mat& src, double angle, Mat& dst)
{
    int len = max(src.cols, src.rows);
    Point2f pt(len/2., len/2.);
    Mat r = getRotationMatrix2D(pt, angle, 1.0);

    warpAffine(src, dst, r, Size(len, len));
}

bool alignImage(Mat& src)
{
	Point upperLeft(51,48);
	Point upperRight(250,49);
	Point lowerLeft(51,250);
	Point lowerRight(250,250);

	Point upperMiddle(199,48);
	Point rightMiddle(250,201);
	Point lowerMiddle(199,250);
	Point leftMiddle(51,201);

	if ( src.at<uchar>(upperMiddle) != 255 || src.at<uchar>(rightMiddle) != 255 || src.at<uchar>(lowerMiddle) != 255 ||
		 src.at<uchar>(leftMiddle) != 255) {
		return false;
	}

	if (src.at<uchar>(upperLeft) == 0 &&
		src.at<uchar>(upperRight) == 255 && src.at<uchar>(lowerLeft) == 255 && src.at<uchar>(lowerRight) == 255) {
//		cout << "upper left\n";
	} else if (src.at<uchar>(upperRight) == 0 &&
			   src.at<uchar>(upperLeft) == 255 && src.at<uchar>(lowerLeft) == 255 && src.at<uchar>(lowerRight) == 255) {
//		cout << "upper right\n";
		rotate(src, 90, src);
	} else if (src.at<uchar>(lowerLeft) == 0 &&
			src.at<uchar>(upperLeft) == 255 && src.at<uchar>(upperRight) == 255 && src.at<uchar>(lowerRight) == 255) {
//		cout << "lower left\n";
		rotate(src, -90, src);
	} else if (src.at<uchar>(lowerRight) == 0 &&
			src.at<uchar>(upperLeft) == 255 && src.at<uchar>(upperRight) == 255 && src.at<uchar>(lowerLeft) == 255) {
//		cout << "lower right\n";
		rotate(src, 180, src);
	} else {
		return false;
	}

	return true;
}

int readCode(Mat& src)
{
	Point p[] = {
			Point(102,100),Point(151,100),Point(200,100),
			Point(102,148),Point(151,148),Point(200,148),
			Point(102,197),Point(151,197),Point(200,197)
	};
	int code = 0;
	for (int i = 0; i < 9; i++) {
		if (src.at<uchar>(p[i]) == 0) {
			code += pow(2,abs(i-8));
		}
	}

	return code;
}

int getCodeFromCard(Mat& region)
{
	// resize image
	resize(region, 300);

	// converting to black/white with threshold 80
	region = region > 80;

	int width = 270;
	int height = 270;
	for (int i = 0; i < region.rows - height; i += 40) {
		for (int j = 0; j < region.cols - width; j += 40) {
			Mat aoi =  Mat(region, Rect(j,i,width,height));

			Mat dst, cdst;
			Canny(aoi, dst, 50, 200, 3);
			cvtColor(dst, cdst, COLOR_GRAY2BGR);

			// determine the border lines
			vector<Vec2f> borderLines;
			findBorderLines(dst, borderLines);

			// determine the four corners
			std::vector<cv::Point2f> corners;
			findCorners(cdst, borderLines, corners);

			// transform perspective
			Mat quad = Mat::zeros(300, 300, CV_8UC3);
			bool success = transformPerspective(aoi, quad, corners);
			if (!success) {
				continue;
			}

			// make sure the image is aligned (rotated) correctly
			success = alignImage(quad);
			if (!success) {
				continue;
			}

			// read code from image
			int code = readCode(quad);
			if (code == 0) {
				continue;
			}

			if (configs["visualMode"] == "true") {
				// debug: display card
				imshow("detected lines", cdst);
				imshow("quadrilateral", quad);
				waitKey();
			}

			return code;
		}
	}

	return -1;
}

int main(int argc, char** argv)
{
	// read config values
	configs = readConfig();

	bool showSpeed = false;
	if (configs["showSpeed"] == "true") {
		showSpeed = true;
	}

	VideoCapture vcap;
	Mat src;

	const string videoStreamAddress = configs["streamAddress"];

	//open the video stream and make sure it's opened
	if(!vcap.open(videoStreamAddress)) {
		cout << "Error opening video stream or file" << endl;
		return -1;
	}

	string jsonStringOld;
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

		imwrite("/dev/shm/detectPlayers.jpg", src);
		src = imread("/dev/shm/detectPlayers.jpg", 0);

		// top left
		Mat region =  Mat(src, Rect(atoi(configs["topLeftX"].c_str()),atoi(configs["topLeftY"].c_str()),
				atoi(configs["topLeftW"].c_str()),atoi(configs["topLeftH"].c_str())));
		int redOffense = getCodeFromCard(region);

		// bottom left
		region =  Mat(src, Rect(atoi(configs["bottomLeftX"].c_str()),atoi(configs["bottomLeftY"].c_str()),
				atoi(configs["bottomLeftW"].c_str()),atoi(configs["bottomLeftH"].c_str())));
		int blueDefense = getCodeFromCard(region);

		// top right
		region =  Mat(src, Rect(atoi(configs["topRightX"].c_str()),atoi(configs["topRightY"].c_str()),
				atoi(configs["topRightW"].c_str()),atoi(configs["topRightH"].c_str())));
		int redDefense = getCodeFromCard(region);

		// bottom right
		region =  Mat(src, Rect(atoi(configs["bottomRightX"].c_str()),atoi(configs["bottomRightY"].c_str()),
				atoi(configs["bottomRightW"].c_str()),atoi(configs["bottomRightH"].c_str())));
		int blueOffense = getCodeFromCard(region);

		stringstream jsonStringNew;
		jsonStringNew << "{\"team\":[{\"blue\":{\"offense\":\""
						 << blueOffense
						 << "\",\"defense\":\""
						 << blueDefense
						 << "\"}},{\"red\":{\"offense\":\""
						 << redOffense
						 << "\",\"defense\":\""
						 << redDefense
						 << "\"}}]}\n";

		if (jsonStringNew.str() != jsonStringOld) {

			string cmd = "curl -X POST -H \"Content-Type: application/json\" "
					   "-d '" + jsonStringNew.str() + "' "
					   + configs["jsonEndpoint"] + ">/dev/null &";
			if (system(cmd.c_str())){}

			jsonFile.open ("/tmp/players.json");
			jsonFile << jsonStringNew.str();
			jsonFile.close();

			jsonStringOld.clear();
			jsonStringOld = String(jsonStringNew.str());
		}

		if (showSpeed) {
			timestamp_t t_end = get_timestamp();
			double secs = (t_end - t_start) / 1000000.0L;
			std::cout << secs << " seconds\n";
		}

		// sleep for 3 second
		usleep(3000000);
	}

	return 0;
}

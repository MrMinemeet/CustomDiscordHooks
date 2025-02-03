// @ts-check
/**
 * This file contains utility functions for other scripts in this repository.
 */

import * as fsp from "node:fs/promises";
import axios from "axios";
import { JSDOM } from "jsdom";

/**
 * Converts a week day number to a string.
 * @param {number} dayNumber A week day number [1, 7]
 * @returns {string} The week day as a string (e.g. 1 -> "Montag", ...)
 */
export function numberToWeekday(dayNumber) {
	if (dayNumber < 0 || 7 < dayNumber) {
		throw new Error("Invalid day number");
	}
	const days = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"];
	return days[dayNumber];
}

/**
 * Loads the discord hooks from a file.
 * @param {string} file
 * @returns {Promise<string[]>}
 * @throws {Error} If the file could not be read
 */
export async function loadHooks(file) {
	try {
		const content = await fsp.readFile(file, "utf-8");
		return content.split("\n").filter((line) => line.trim() !== "");
	} catch (err) {
		throw new Error(`Failed to load hooks from file: ${err}`);
	}
}

/**
 * Sends a message to a discord webhook.
 * @param {string} hook The URL of the discord webhook
 * @param {string} message The message to send
 * @returns {Promise<void>}
 */
export async function sendMessage(hook, message) {
	return new Promise((resolve, reject) => {
		axios.post(hook, {
			content: message
		}).then(() => {
			resolve();
		}).catch((err) => {
			reject(new Error(`Failed to send message to discord webhook: ${err}`));
		});
	});
}

/**
 * Fetches the page body from a URL and returns it as a JSDOM object.
 * @param {string} url The URL to fetch the page body from
 * @returns { Promise<JSDOM | null> } The page body as a JSDOM object or null if the page could not be fetched
 */
export async function getPagebody(url) {
	try {
		const html = (await axios.get(url)).data;
		return new JSDOM(html.replace(/<style[^>]*>[\s\S]*?<\/style>/gi, ""));
	} catch (error) {
		console.error("Error fetching JKU Mensa", error);
		return null;
	}
}
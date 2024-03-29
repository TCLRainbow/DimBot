--name: add-translator-convo!
INSERT INTO TranslatorConvo
VALUES (:user, :ch, :topic);

--name: join-translator-convo!
INSERT INTO TranslatorParticipant
VALUES (:creator, :ch, :participant);

--name: clean-translator-convo!
-- creator should be the old one
DELETE FROM TranslatorConvo
WHERE NOT EXISTS(
    SELECT 1 FROM TranslatorParticipant
    WHERE creatorID = :creator AND channelID = :ch
) AND creatorID = :creator AND channelID = :ch;

--name: remove-translator-convo!
DELETE FROM TranslatorConvo
WHERE creatorID = :creator AND channelID = :ch;

--name: get-translator-topic$
SELECT topic FROM TranslatorConvo
WHERE creatorID = :creator AND channelID = :ch;

--name: update-translator-topic
-- NOTE THAT THIS QUERY HAS NO ! OPERATOR!!!
UPDATE TranslatorConvo
SET topic = :topic
WHERE channelID = :ch AND creatorID = :creator
AND EXISTS(
    SELECT 1 FROM TranslatorParticipant
    WHERE creatorID = :creator AND channelID = :ch AND participantID = :creator
);

--name: get-translator-participant-creator$
SELECT creatorID
FROM TranslatorParticipant
WHERE channelID = :ch AND participantID = :participant;

--name: get-translator-convo-by-participant^
SELECT
    TC.creatorID,
    topic
FROM
    TranslatorConvo TC
INNER JOIN
    TranslatorParticipant TP ON TC.creatorID = TP.creatorID AND TC.channelID = TP.channelID
WHERE
    TP.channelID = :ch AND TP.participantID = :participant;

--name: update-translator-participant!
UPDATE TranslatorParticipant
SET creatorID = :creator
WHERE channelID = :ch AND participantID = :participant;

--name: remove-translator-participant!
DELETE FROM TranslatorParticipant
WHERE channelID = :ch AND participantID = :participant;

--name: kick-translator-participant!
DELETE FROM TranslatorParticipant
WHERE creatorID = :creator AND channelID = :ch AND participantID = :participant;

--name: get-translator-participants-locale
SELECT
    participantID,
    LocalePref AS LocalePref -- coalesce()
FROM
    TranslatorParticipant
LEFT JOIN
    UserCfg ON participantID = ID
WHERE
    creatorID = :creator AND channelID = :ch;